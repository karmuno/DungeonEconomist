import math
import random
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import (
    Adventurer, AdventurerClass, Party, Expedition, Keep,
    ExpeditionNodeResult, ExpeditionLog, party_adventurer,
)
from app.schemas import GameTimeInfo, AdvanceDayResult, GameEvent
from app.auth import get_current_keep
from app.names import generate_adventurer_name
from app.dungeons import DUNGEON_LEVEL_NAMES, DUNGEON_LEVELS
from app.routes.expeditions import resolve_expedition, _finalize_expedition

router = APIRouter()

# Recruitment chance per class per day (~2.3%)
RECRUITMENT_CHANCE = 0.023
MAX_TAVERN_SIZE = 20


def roll_hp(adventurer_class: AdventurerClass) -> int:
    """Roll starting HP for an adventurer"""
    base = random.randint(1, 6)
    if adventurer_class in (AdventurerClass.FIGHTER, AdventurerClass.DWARF):
        return base + 2
    return base


def create_random_adventurer(adventurer_class: AdventurerClass, keep: Keep, db: Session) -> Adventurer:
    """Create a new level 1 adventurer of the given class"""
    hp = roll_hp(adventurer_class)
    adv = Adventurer(
        keep_id=keep.id,
        name=generate_adventurer_name(adventurer_class),
        adventurer_class=adventurer_class,
        level=1,
        xp=0,
        hp_max=hp,
        hp_current=hp,
        gold=0,
        is_available=True,
    )
    db.add(adv)
    return adv


def run_daily_recruitment(keep: Keep, db: Session) -> list:
    """Run daily recruitment rolls. Returns list of new adventurers created."""
    from app.models import Building
    from app.buildings import BUILDING_CONFIG, has_recruitment_bonus

    # Tavern count: available + on_expedition only (not dead, bankrupt, or assigned)
    active_count = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
        Adventurer.is_assigned == False,
    ).count()

    # Build a set of classes that get doubled recruitment from buildings
    boosted_classes = set()
    buildings = db.query(Building).filter(Building.keep_id == keep.id).all()
    for b in buildings:
        if has_recruitment_bonus(b.building_type):
            class_name = BUILDING_CONFIG.get(b.building_type, {}).get("class", "")
            boosted_classes.add(class_name)

    new_adventurers = []
    for adv_class in AdventurerClass:
        if active_count >= MAX_TAVERN_SIZE:
            break
        # Double chance if building exists for this class
        chance = RECRUITMENT_CHANCE
        if adv_class.value in boosted_classes:
            chance = chance * 2
        # Geometric re-rolls: keep rolling while successful
        while random.random() < chance:
            if active_count >= MAX_TAVERN_SIZE:
                break
            adv = create_random_adventurer(adv_class, keep, db)
            new_adventurers.append(adv)
            active_count += 1

    return new_adventurers


def format_currency(gold: int, silver: int, copper: int) -> str:
    """Format currency as a human-readable string like '2gp 3sp 5cp'."""
    parts = []
    if gold > 0:
        parts.append(f"{gold}gp")
    if silver > 0:
        parts.append(f"{silver}sp")
    if copper > 0:
        parts.append(f"{copper}cp")
    return " ".join(parts) if parts else "0cp"


def copper_to_parts(total_copper: int) -> tuple[int, int, int]:
    """Convert a copper amount to (gold, silver, copper) tuple."""
    g = total_copper // 100
    s = (total_copper % 100) // 10
    c = total_copper % 10
    return g, s, c


def process_upkeep(keep: Keep, db: Session) -> list[GameEvent]:
    """
    Run monthly upkeep if current_day is a multiple of 30.
    Upkeep cost is 1 cp per XP (floored). If adventurer cannot pay, they are
    permanently removed to debtor's prison.
    Returns list of events.
    """
    if keep.current_day == 0 or keep.current_day % 30 != 0:
        return []

    events: list[GameEvent] = []

    # Only process active (non-dead, non-bankrupt) adventurers not on expedition
    adventurers = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
        Adventurer.on_expedition == False,
    ).all()
    total_copper_transferred = 0
    bankrupt_count = 0

    for adv in adventurers:
        # Upkeep cost: 1 copper per XP
        cost_copper = math.floor(adv.xp * 1)

        if cost_copper <= 0:
            continue

        if adv.total_copper() >= cost_copper:
            adv.subtract_currency(cost_copper)
            keep.add_treasury(cost_copper)
            keep.total_score += cost_copper
            total_copper_transferred += cost_copper
        else:
            # Sacrifice all magic items to skip upkeep entirely this month
            if adv.magic_items:
                item_names = [item.name for item in adv.magic_items]
                for item in list(adv.magic_items):
                    db.delete(item)
                events.append(GameEvent(
                    type="upkeep",
                    message=f"{adv.name} sacrificed magic items to avoid debtor's prison: {', '.join(item_names)}"
                ))
                continue

            # Bankruptcy is permanent — adventurer goes to debtor's prison
            remaining = adv.total_copper()
            if remaining > 0:
                keep.add_treasury(remaining)
                keep.total_score += remaining
                total_copper_transferred += remaining

            # Sell any remaining items for treasury
            for item in list(adv.magic_items):
                db.delete(item)

            adv.gold = 0
            adv.silver = 0
            adv.copper = 0
            adv.is_bankrupt = True
            adv.bankruptcy_day = keep.current_day
            adv.is_available = False
            adv.on_expedition = False
            bankrupt_count += 1

            # Remove from all parties
            adv.parties = []

            events.append(GameEvent(
                type="upkeep",
                message=f"{adv.name} went bankrupt and was sent to debtor's prison"
            ))

    if total_copper_transferred > 0:
        g, s, c = copper_to_parts(total_copper_transferred)
        events.insert(0, GameEvent(
            type="upkeep",
            message=f"Upkeep day! {format_currency(g, s, c)} collected to treasury"
        ))
    else:
        events.insert(0, GameEvent(
            type="upkeep",
            message="Upkeep day! No gold collected (adventurers have no XP costs yet)"
        ))

    return events


def heal_adventurer(adv: Adventurer, hp_per_day: int = 1) -> bool:
    """Heal an adventurer. Returns True if fully healed this tick."""
    was_injured = adv.hp_current < adv.hp_max
    adv.hp_current = min(adv.hp_current + hp_per_day, adv.hp_max)
    if was_injured and adv.hp_current == adv.hp_max:
        adv.is_available = True
        return True
    return False


def _get_temple_healing_bonus(keep: Keep, db: Session) -> int:
    """Get bonus HP/day from temple (1 per assigned Cleric)."""
    from app.models import Building
    temple = db.query(Building).filter(
        Building.keep_id == keep.id,
        Building.building_type == "temple",
    ).first()
    if not temple:
        return 0
    return len(temple.assigned_adventurers)


def _advance_one_day(keep: Keep, db: Session) -> list[GameEvent]:
    """Advance game time by one day and return events. Does not commit."""
    events: list[GameEvent] = []

    keep.current_day += 1
    keep.last_updated = datetime.now()

    # Calculate healing rate (base 1 + temple bonus)
    temple_bonus = _get_temple_healing_bonus(keep, db)
    hp_per_day = 1 + temple_bonus

    # Daily healing
    healing_adventurers = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.on_expedition == False,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
        Adventurer.hp_current < Adventurer.hp_max,
    ).all()
    for adv in healing_adventurers:
        if heal_adventurer(adv, hp_per_day):
            events.append(GameEvent(
                type="healing",
                message=f"{adv.name} fully recovered and is available",
            ))

    # Daily recruitment
    new_recruits = run_daily_recruitment(keep, db)
    for adv in new_recruits:
        events.append(GameEvent(
            type="recruitment",
            message=f"{adv.name} ({adv.adventurer_class.value}) arrived at the tavern"
        ))

    # Auto-resolve any awaiting_choice expeditions from PREVIOUS days
    # (player skipped the decision — the party decides on its own)
    from app.expedition_events import auto_decide
    awaiting = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
        Expedition.result == "awaiting_choice",
    ).all()
    newly_awaiting_ids: set[int] = set()
    for expedition in awaiting:
        party_name = expedition.party.name if expedition.party else "Unknown"
        dp = expedition.pending_event or {}
        choice = auto_decide(dp.get("type", ""), expedition.party.members if expedition.party else [])

        # Apply the auto-decision
        sim_result = expedition.simulation_data or {}
        decision_points = sim_result.get("decision_points", [])
        resolved = expedition.resolved_phases or 0

        if choice == "retreat":
            result = _finalize_expedition(expedition, sim_result, db, keep, retreat=True)
            events.append(GameEvent(
                type="expedition_complete",
                message=f"Party '{party_name}' decided to retreat: {dp.get('message', '')}",
                expedition_id=expedition.id,
            ))
            for evt in result.get("events", []):
                events.append(GameEvent(type=evt["type"], message=evt["message"]))
        else:
            # Press on
            expedition.resolved_phases = resolved + 1
            expedition.pending_event = None
            if expedition.resolved_phases < len(decision_points):
                expedition.decision_day = expedition.return_day
            else:
                expedition.decision_day = None
            expedition.result = "in_progress"
            events.append(GameEvent(
                type="expedition_choice",
                message=f"Party '{party_name}' pressed on: {dp.get('message', '')}",
                expedition_id=expedition.id,
            ))

    # Process in-progress expedition events (scoped via Party.keep_id)
    active_expeditions = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
        Expedition.result == "in_progress",
    ).all()
    for expedition in active_expeditions:
        party_name = expedition.party.name if expedition.party else "Unknown"

        # Check if a mid-expedition decision is due
        if (expedition.decision_day
                and expedition.decision_day <= keep.current_day):
            sim_result = expedition.simulation_data or {}
            decision_points = sim_result.get("decision_points", [])
            resolved = expedition.resolved_phases or 0
            if resolved < len(decision_points):
                dp = decision_points[resolved]
                expedition.result = "awaiting_choice"
                expedition.pending_event = dp
                events.append(GameEvent(
                    type="expedition_choice",
                    message=f"Party '{party_name}': {dp.get('message', 'A decision awaits')}",
                    expedition_id=expedition.id,
                ))
                continue

        # Check if expedition has returned
        if expedition.return_day <= keep.current_day:
            resolution = resolve_expedition(expedition, db, keep)

            if resolution.get("awaiting_choice"):
                pending = resolution.get("pending_event", {})
                events.append(GameEvent(
                    type="expedition_choice",
                    message=f"Party '{party_name}': {pending.get('message', 'A decision awaits')}",
                    expedition_id=expedition.id,
                ))
            else:
                events.append(GameEvent(
                    type="expedition_complete",
                    message=f"Party '{party_name}' returned from expedition",
                    expedition_id=expedition.id,
                ))
                for evt in resolution.get("events", []):
                    events.append(GameEvent(type=evt["type"], message=evt["message"]))

    # Monthly upkeep (every 30 days)
    upkeep_events = process_upkeep(keep, db)
    events.extend(upkeep_events)

    return events


# Event types that are considered notable for skip-to-event
NOTABLE_EVENT_TYPES = {"recruitment", "expedition_complete", "expedition_choice", "death", "upkeep", "loot"}


def _check_pending_decisions(keep: Keep, db: Session) -> list[GameEvent]:
    """Check for awaiting_choice expeditions. If any exist, return their events
    without advancing time. Returns empty list if no decisions pending."""
    awaiting = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
        Expedition.result == "awaiting_choice",
    ).all()
    events = []
    for expedition in awaiting:
        party_name = expedition.party.name if expedition.party else "Unknown"
        dp = expedition.pending_event or {}
        events.append(GameEvent(
            type="expedition_choice",
            message=f"Party '{party_name}': {dp.get('message', 'A decision awaits')}",
            expedition_id=expedition.id,
        ))
    return events


@router.post("/time/advance-day", response_model=AdvanceDayResult)
def advance_day(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """Advances the game time by one day. Blocks if a decision is pending."""
    # Block if there's a pending decision
    pending = _check_pending_decisions(keep, db)
    if pending:
        return AdvanceDayResult(
            current_day=keep.current_day,
            day_started_at=keep.day_started_at,
            last_updated=keep.last_updated,
            events=pending,
        )

    events = _advance_one_day(keep, db)

    db.commit()
    db.refresh(keep)

    return AdvanceDayResult(
        current_day=keep.current_day,
        day_started_at=keep.day_started_at,
        last_updated=keep.last_updated,
        events=events,
    )


@router.post("/time/skip-to-event", response_model=AdvanceDayResult)
def skip_to_event(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """Advance days until a notable event occurs (max 30 days). Blocks if decision pending."""
    # Block if there's a pending decision
    pending = _check_pending_decisions(keep, db)
    if pending:
        return AdvanceDayResult(
            current_day=keep.current_day,
            day_started_at=keep.day_started_at,
            last_updated=keep.last_updated,
            events=pending,
        )

    MAX_SKIP = 30
    all_events: list[GameEvent] = []

    for _ in range(MAX_SKIP):
        day_events = _advance_one_day(keep, db)
        all_events.extend(day_events)
        if any(e.type in NOTABLE_EVENT_TYPES for e in day_events):
            break

    db.commit()
    db.refresh(keep)

    return AdvanceDayResult(
        current_day=keep.current_day,
        day_started_at=keep.day_started_at,
        last_updated=keep.last_updated,
        events=all_events,
    )


@router.get("/dashboard/stats")
def get_dashboard_stats(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """Get aggregated dashboard stats for the home page."""
    adventurer_count = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
    ).count()
    party_count = db.query(Party).filter(Party.keep_id == keep.id).count()
    expedition_count = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(Party.keep_id == keep.id).count()

    graveyard_count = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_dead == True,
    ).count()
    debtors_prison_count = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_bankrupt == True,
    ).count()

    active_expeditions = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
        Expedition.result == "in_progress",
    ).all()
    recent_expeditions = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
    ).order_by(Expedition.started_at.desc()).limit(5).all()

    return {
        "adventurer_count": adventurer_count,
        "graveyard_count": graveyard_count,
        "debtors_prison_count": debtors_prison_count,
        "party_count": party_count,
        "expedition_count": expedition_count,
        "treasury_gold": keep.treasury_gold,
        "treasury_silver": keep.treasury_silver,
        "treasury_copper": keep.treasury_copper,
        "total_score": keep.total_score,
        "current_day": keep.current_day,
        "active_expeditions": [
            {
                "id": e.id,
                "party_id": e.party_id,
                "start_day": e.start_day,
                "return_day": e.return_day,
                "result": e.result,
            }
            for e in active_expeditions
        ],
        "recent_expeditions": [
            {
                "id": e.id,
                "party_name": e.party.name if e.party else "Unknown",
                "dungeon_level": e.dungeon_level or 1,
                "start_day": e.start_day,
                "return_day": e.return_day,
                "duration_days": e.duration_days,
                "result": e.result,
                "treasure_total": (e.simulation_data or {}).get("treasure_total", 0),
                "xp_earned": (e.simulation_data or {}).get("xp_earned", 0),
            }
            for e in recent_expeditions
        ],
    }


@router.get("/time/", response_model=GameTimeInfo)
def get_game_time(keep: Keep = Depends(get_current_keep)):
    """Get current game time for the active keep."""
    return GameTimeInfo(
        current_day=keep.current_day,
        day_started_at=keep.day_started_at,
        last_updated=keep.last_updated,
    )


@router.get("/dungeon/")
def get_dungeon_info(keep: Keep = Depends(get_current_keep)):
    """Get the keep's megadungeon info: name, unlocked levels, level names."""
    total_levels = len(DUNGEON_LEVELS)
    levels = []
    for i in range(total_levels):
        level_num = i + 1
        lvl = DUNGEON_LEVELS[i]
        levels.append({
            "level": level_num,
            "name": lvl["name"],
            "duration_days": lvl["duration_days"],
            "unlocked": level_num <= keep.max_dungeon_level,
        })
    return {
        "dungeon_name": keep.dungeon_name,
        "max_dungeon_level": keep.max_dungeon_level,
        "total_levels": total_levels,
        "levels": levels,
    }

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
from app.routes.expeditions import resolve_expedition

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
    # Count current active adventurers (not dead, not bankrupt)
    active_count = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
    ).count()

    new_adventurers = []
    for adv_class in AdventurerClass:
        if active_count >= MAX_TAVERN_SIZE:
            break
        # Geometric re-rolls: keep rolling while successful
        while random.random() < RECRUITMENT_CHANCE:
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
            # Bankruptcy is permanent — adventurer goes to debtor's prison
            remaining = adv.total_copper()
            if remaining > 0:
                keep.add_treasury(remaining)
                keep.total_score += remaining
                total_copper_transferred += remaining

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


def heal_adventurer(adv: Adventurer, days: int = 1) -> bool:
    """Heal an adventurer by 1 HP per day. Returns True if fully healed this tick."""
    was_injured = adv.hp_current < adv.hp_max
    for _ in range(days):
        if adv.hp_current >= adv.hp_max:
            break
        adv.hp_current = min(adv.hp_current + 1, adv.hp_max)
    if was_injured and adv.hp_current == adv.hp_max:
        adv.is_available = True
        return True
    return False


def _advance_one_day(keep: Keep, db: Session) -> list[GameEvent]:
    """Advance game time by one day and return events. Does not commit."""
    events: list[GameEvent] = []

    keep.current_day += 1
    keep.last_updated = datetime.now()

    # Daily healing
    healing_adventurers = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.on_expedition == False,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
        Adventurer.hp_current < Adventurer.hp_max,
    ).all()
    for adv in healing_adventurers:
        if heal_adventurer(adv):
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

    # Process expedition completions (scoped via Party.keep_id)
    active_expeditions_to_check = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
        Expedition.result == "in_progress",
    ).all()
    for expedition in active_expeditions_to_check:
        if expedition.return_day <= keep.current_day:
            party_name = expedition.party.name if expedition.party else "Unknown"

            # Apply simulation results (XP, loot, deaths, etc.)
            resolution = resolve_expedition(expedition, db, keep)

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
NOTABLE_EVENT_TYPES = {"recruitment", "expedition_complete", "death", "upkeep", "loot"}


@router.post("/time/advance-day", response_model=AdvanceDayResult)
def advance_day(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """Advances the game time by one day and updates expedition statuses."""
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
    """Advance days until a notable event occurs (max 30 days)."""
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
                "party_id": e.party_id,
                "party_name": e.party.name if e.party else "Unknown",
                "start_day": e.start_day,
                "return_day": e.return_day,
                "duration_days": e.duration_days,
                "result": e.result,
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "finished_at": e.finished_at.isoformat() if e.finished_at else None,
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

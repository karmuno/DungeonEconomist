import math
import random
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Adventurer, AdventurerClass, Party, Expedition, Player, GameTime
from app.schemas import GameTimeInfo, AdvanceDayResult, GameEvent
from app.routes.expeditions import resolve_expedition

router = APIRouter()

# Recruitment chance per class per day (~2.3%)
RECRUITMENT_CHANCE = 0.023
MAX_TAVERN_SIZE = 20


def generate_adventurer_name(adventurer_class: AdventurerClass) -> str:
    """Generate a random name for a new adventurer"""
    first_names = {
        AdventurerClass.FIGHTER: ["Valerius", "Galen", "Rurik", "Thaddeus", "Elira", "Brynn", "Kord", "Sigrid"],
        AdventurerClass.CLERIC: ["Brother Malric", "Sister Mirabel", "Seraphine", "Father Aldric", "Deacon Theron", "Priestess Yara"],
        AdventurerClass.MAGIC_USER: ["Kael", "Vespera", "Tamsin", "Mordecai", "Isolde", "Zephyr", "Arcanus"],
        AdventurerClass.ELF: ["Lirael", "Sylwen", "Eldrin", "Aelindra", "Thalion", "Caelum", "Elowen"],
        AdventurerClass.DWARF: ["Borin", "Durgan", "Helga", "Thorin", "Gimra", "Brokk", "Dagna"],
        AdventurerClass.HOBBIT: ["Milo", "Fira", "Pip", "Nimble Nissa", "Rosie", "Tuck", "Bramble"],
    }
    surnames = [
        "Swiftblade", "Stonefist", "Dawnstar", "Underbough", "Moonshadow",
        "Starfall", "Oakenshield", "Bramble", "Silverleaf", "Stonehammer",
        "Nightshade", "Axeborn", "Ironbeard", "Quickfoot", "Willow",
        "Firebrand", "Stormcrow", "Brightwater", "Shadowmend", "Thornwall",
    ]
    first = random.choice(first_names.get(adventurer_class, ["Unknown"]))
    # Some names already have two parts (e.g., "Brother Malric")
    if " " in first:
        return first
    return f"{first} {random.choice(surnames)}"


def roll_hp(adventurer_class: AdventurerClass) -> int:
    """Roll starting HP for an adventurer"""
    base = random.randint(1, 6)
    if adventurer_class in (AdventurerClass.FIGHTER, AdventurerClass.DWARF):
        return base + 2
    return base


def create_random_adventurer(adventurer_class: AdventurerClass, db: Session) -> Adventurer:
    """Create a new level 1 adventurer of the given class"""
    hp = roll_hp(adventurer_class)
    adv = Adventurer(
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


def run_daily_recruitment(db: Session) -> list:
    """Run daily recruitment rolls. Returns list of new adventurers created."""
    # Count current active adventurers (not dead, not bankrupt)
    active_count = db.query(Adventurer).filter(
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
            adv = create_random_adventurer(adv_class, db)
            new_adventurers.append(adv)
            active_count += 1

    return new_adventurers


def auto_start_day_one(db: Session) -> list:
    """If no adventurers exist on day 1, generate a starting party of 6 (one per class)."""
    adventurer_count = db.query(Adventurer).count()
    if adventurer_count > 0:
        return []

    # Ensure a default player exists
    player = db.query(Player).first()
    if not player:
        player = Player(name="Default Player", treasury_gold=0, treasury_silver=0, treasury_copper=0, total_score=0)
        db.add(player)

    new_adventurers = []
    for adv_class in AdventurerClass:
        adv = create_random_adventurer(adv_class, db)
        new_adventurers.append(adv)

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


def process_upkeep(db: Session, current_day: int) -> list[GameEvent]:
    """
    Run monthly upkeep if current_day is a multiple of 30.
    Upkeep cost is 1 cp per XP (floored). If adventurer cannot pay, they are
    permanently removed to debtor's prison.
    Returns list of events.
    """
    if current_day == 0 or current_day % 30 != 0:
        return []

    events: list[GameEvent] = []

    player = db.query(Player).first()
    if not player:
        player = Player(name="Default Player", treasury_gold=0, treasury_silver=0, treasury_copper=0, total_score=0)
        db.add(player)
        db.flush()

    # Only process active (non-dead, non-bankrupt) adventurers
    adventurers = db.query(Adventurer).filter(
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
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
            player.add_treasury(cost_copper)
            player.total_score += cost_copper
            total_copper_transferred += cost_copper
        else:
            # Bankruptcy is permanent — adventurer goes to debtor's prison
            remaining = adv.total_copper()
            if remaining > 0:
                player.add_treasury(remaining)
                player.total_score += remaining
                total_copper_transferred += remaining

            adv.gold = 0
            adv.silver = 0
            adv.copper = 0
            adv.is_bankrupt = True
            adv.bankruptcy_day = current_day
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


def heal_adventurer(adv: Adventurer, days: int = 1) -> list[GameEvent]:
    """Heal an adventurer by 1 HP per day. Returns events if fully healed."""
    events: list[GameEvent] = []
    for _ in range(days):
        if adv.hp_current >= adv.hp_max:
            break
        adv.hp_current = min(adv.hp_current + 1, adv.hp_max)
    if adv.hp_current == adv.hp_max:
        adv.is_available = True
        events.append(GameEvent(
            type="healing",
            message=f"{adv.name} fully recovered and is available"
        ))
    return events


@router.post("/time/advance-day", response_model=AdvanceDayResult)
def advance_day(db: Session = Depends(get_db)):
    """Advances the game time by one day and updates expedition statuses."""
    events: list[GameEvent] = []

    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=0, day_started_at=datetime.now(), last_updated=datetime.now())
        db.add(game_time)

    game_time.current_day += 1
    game_time.last_updated = datetime.now()

    # Daily healing
    healing_adventurers = db.query(Adventurer).filter(
        Adventurer.on_expedition == False,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
        Adventurer.hp_current < Adventurer.hp_max,
    ).all()
    for adv in healing_adventurers:
        heal_events = heal_adventurer(adv)
        events.extend(heal_events)

    # Daily recruitment
    new_recruits = run_daily_recruitment(db)
    for adv in new_recruits:
        events.append(GameEvent(
            type="recruitment",
            message=f"{adv.name} ({adv.adventurer_class.value}) arrived at the tavern"
        ))

    # Process expedition completions
    active_expeditions_to_check = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    for expedition in active_expeditions_to_check:
        if expedition.return_day <= game_time.current_day:
            party_name = expedition.party.name if expedition.party else "Unknown"

            # Apply simulation results (XP, loot, deaths, etc.)
            resolution = resolve_expedition(expedition, db, game_time.current_day)

            events.append(GameEvent(
                type="expedition_complete",
                message=f"Party '{party_name}' returned from expedition"
            ))
            for evt in resolution.get("events", []):
                events.append(GameEvent(type=evt["type"], message=evt["message"]))

    # Monthly upkeep (every 30 days)
    upkeep_events = process_upkeep(db, game_time.current_day)
    events.extend(upkeep_events)

    db.commit()
    db.refresh(game_time)

    return AdvanceDayResult(
        current_day=game_time.current_day,
        day_started_at=game_time.day_started_at,
        last_updated=game_time.last_updated,
        events=events,
    )


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get aggregated dashboard stats for the home page."""
    adventurer_count = db.query(Adventurer).filter(
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
    ).count()
    party_count = db.query(Party).count()
    expedition_count = db.query(Expedition).count()

    graveyard_count = db.query(Adventurer).filter(Adventurer.is_dead == True).count()
    debtors_prison_count = db.query(Adventurer).filter(Adventurer.is_bankrupt == True).count()

    game_time = ensure_game_initialized(db)

    player = db.query(Player).first()

    active_expeditions = db.query(Expedition).filter(
        Expedition.result == "in_progress"
    ).all()
    recent_expeditions = db.query(Expedition).order_by(
        Expedition.started_at.desc()
    ).limit(5).all()

    return {
        "adventurer_count": adventurer_count,
        "graveyard_count": graveyard_count,
        "debtors_prison_count": debtors_prison_count,
        "party_count": party_count,
        "expedition_count": expedition_count,
        "treasury_gold": player.treasury_gold if player else 0,
        "treasury_silver": player.treasury_silver if player else 0,
        "treasury_copper": player.treasury_copper if player else 0,
        "total_score": player.total_score if player else 0,
        "current_day": game_time.current_day,
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


@router.get("/adventurers/graveyard")
def get_graveyard(db: Session = Depends(get_db)):
    """List all dead adventurers"""
    dead = db.query(Adventurer).filter(Adventurer.is_dead == True).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "class": a.adventurer_class.value,
            "level": a.level,
            "death_day": a.death_day,
        }
        for a in dead
    ]


@router.get("/adventurers/debtors-prison")
def get_debtors_prison(db: Session = Depends(get_db)):
    """List all bankrupt adventurers"""
    bankrupt = db.query(Adventurer).filter(Adventurer.is_bankrupt == True).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "class": a.adventurer_class.value,
            "level": a.level,
            "bankruptcy_day": a.bankruptcy_day,
        }
        for a in bankrupt
    ]


def ensure_game_initialized(db: Session) -> GameTime:
    """Ensure GameTime, Player, and starting adventurers exist."""
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=0, day_started_at=datetime.now(), last_updated=datetime.now())
        db.add(game_time)

        # Ensure default player
        player = db.query(Player).first()
        if not player:
            player = Player(name="Default Player", treasury_gold=0, treasury_silver=0, treasury_copper=0, total_score=0)
            db.add(player)

        # Auto-generate starting adventurers
        auto_start_day_one(db)

        db.commit()
        db.refresh(game_time)
    return game_time


@router.get("/time/", response_model=GameTimeInfo)
def get_game_time(db: Session = Depends(get_db)):
    """Get current game time"""
    game_time = ensure_game_initialized(db)
    return game_time

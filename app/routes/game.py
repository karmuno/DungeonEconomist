import math
import random
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Adventurer, AdventurerClass, Party, Expedition, Player, GameTime
from app.schemas import GameTimeInfo

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

    new_adventurers = []
    for adv_class in AdventurerClass:
        adv = create_random_adventurer(adv_class, db)
        new_adventurers.append(adv)

    return new_adventurers


@router.put("/upkeep")
def run_upkeep(db: Session = Depends(get_db)):
    """
    Run monthly upkeep. If current_day is a multiple of 30, charge upkeep costs.
    Upkeep cost is 1% of XP (floored). If adventurer cannot pay, they are
    permanently removed to debtor's prison.
    """
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

    # Ensure a default player exists
    player = db.query(Player).first()
    if not player:
        player = Player(name="Default Player", treasury=0, total_score=0)
        db.add(player)
        db.commit()
        db.refresh(player)

    if game_time.current_day % 30 == 0:
        # Only process active (non-dead, non-bankrupt) adventurers
        adventurers = db.query(Adventurer).filter(
            Adventurer.is_dead == False,
        ).all()
        adventurers_processed = 0
        bankrupt_adventurers = 0
        total_gold_deducted_from_adventurers = 0
        total_gold_transferred_to_treasury = 0

        for adv in adventurers:
            adventurers_processed += 1
            cost = math.floor(adv.xp * 0.01)

            if cost <= 0:
                continue

            if adv.gold >= cost:
                adv.gold -= cost
                total_gold_deducted_from_adventurers += cost

                player.treasury += cost
                player.total_score += cost
                total_gold_transferred_to_treasury += cost
            else:
                # Bankruptcy is permanent — adventurer goes to debtor's prison
                if adv.gold > 0:
                    player.treasury += adv.gold
                    player.total_score += adv.gold
                    total_gold_transferred_to_treasury += adv.gold
                    total_gold_deducted_from_adventurers += adv.gold

                adv.gold = 0
                adv.is_bankrupt = True
                adv.bankruptcy_day = game_time.current_day
                adv.is_available = False
                adv.on_expedition = False
                bankrupt_adventurers += 1

                # Remove from all parties
                adv.parties = []

        db.commit()
        return {
            "message": f"Upkeep applied for day {game_time.current_day}. "
                       f"{adventurers_processed} adventurers processed. "
                       f"{bankrupt_adventurers} became bankrupt. "
                       f"Total gold deducted from adventurers: {total_gold_deducted_from_adventurers} GP. "
                       f"Total gold transferred to player treasury: {total_gold_transferred_to_treasury} GP."
        }
    else:
        return {
            "message": f"No upkeep applied for day {game_time.current_day}. "
                       "Upkeep runs every 30 days."
        }


@router.post("/time/advance-day", response_model=GameTimeInfo)
def advance_day(db: Session = Depends(get_db)):
    """Advances the game time by one day and updates expedition statuses."""
    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=0, day_started_at=datetime.now(), last_updated=datetime.now())
        db.add(game_time)

    game_time.current_day += 1
    game_time.last_updated = datetime.now()

    # Day 1 auto-start: generate starting adventurers if none exist
    if game_time.current_day == 1:
        new_starters = auto_start_day_one(db)
        if new_starters:
            db.flush()

    # Daily healing: all non-expedition, non-dead, non-bankrupt adventurers heal 1 HP/day
    healing_adventurers = db.query(Adventurer).filter(
        Adventurer.on_expedition == False,
        Adventurer.is_dead == False,
        Adventurer.is_bankrupt == False,
        Adventurer.hp_current < Adventurer.hp_max,
    ).all()
    for adv in healing_adventurers:
        adv.hp_current = min(adv.hp_current + 1, adv.hp_max)
        if adv.hp_current == adv.hp_max:
            adv.is_available = True

    # Daily recruitment
    run_daily_recruitment(db)

    # Process expedition completions
    active_expeditions_to_check = db.query(Expedition).filter(Expedition.result == "in_progress").all()
    for expedition in active_expeditions_to_check:
        if expedition.return_day <= game_time.current_day:
            expedition.result = "completed"
            expedition.finished_at = datetime.now()

            if expedition.party:
                expedition.party.on_expedition = False
                for adventurer in expedition.party.members:
                    adventurer.on_expedition = False
                    # Don't set available — they need to heal to full HP first
                    adventurer.is_available = (adventurer.hp_current == adventurer.hp_max)

    db.commit()
    db.refresh(game_time)

    return GameTimeInfo(
        current_day=game_time.current_day,
        day_started_at=game_time.day_started_at,
        last_updated=game_time.last_updated
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

    player = db.query(Player).first()
    if not player:
        player = Player(name="Default Player", treasury=0, total_score=0)
        db.add(player)
        db.commit()
        db.refresh(player)

    game_time = db.query(GameTime).first()
    if not game_time:
        game_time = GameTime(current_day=1)
        db.add(game_time)
        db.commit()
        db.refresh(game_time)

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
        "treasury": player.treasury,
        "total_score": player.total_score,
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


@router.get("/time/", response_model=GameTimeInfo)
def get_game_time(db: Session = Depends(get_db)):
    """Get current game time"""
    game_time = db.query(GameTime).first()
    if not game_time:
        raise HTTPException(status_code=404, detail="Game time not initialized")
    return game_time

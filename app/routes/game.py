import math
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Adventurer, Party, Expedition, Player, GameTime
from app.schemas import GameTimeInfo

router = APIRouter()


@router.put("/upkeep")
def run_upkeep(db: Session = Depends(get_db)):
    """
    Run daily upkeep tasks.
    If current_day is a multiple of 30, charge upkeep costs to adventurers.
    Upkeep cost is 1% of XP (floored). If adventurer cannot pay, they go bankrupt.
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
        adventurers = db.query(Adventurer).all()
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

                if adv.is_bankrupt:
                    adv.is_bankrupt = False
                    adv.expedition_status = "resting"
            else:
                if adv.gold > 0:
                    player.treasury += adv.gold
                    player.total_score += adv.gold
                    total_gold_transferred_to_treasury += adv.gold
                    total_gold_deducted_from_adventurers += adv.gold

                adv.gold = 0
                adv.is_bankrupt = True
                adv.expedition_status = "Bankrupt"
                bankrupt_adventurers += 1

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
                    adventurer.is_available = True

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
    adventurer_count = db.query(Adventurer).count()
    party_count = db.query(Party).count()
    expedition_count = db.query(Expedition).count()

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


@router.get("/time/", response_model=GameTimeInfo)
def get_game_time(db: Session = Depends(get_db)):
    """Get current game time"""
    game_time = db.query(GameTime).first()
    if not game_time:
        raise HTTPException(status_code=404, detail="Game time not initialized")
    return game_time

import math
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request
from datetime import datetime

from app.database import get_db
from app.models import Adventurer, Expedition, Player, GameTime
from app.schemas import GameTimeInfo

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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


@router.post("/time/advance-day")
def advance_day(request: Request, db: Session = Depends(get_db)):
    """Advances the game time by one day and updates expedition statuses.
    Returns HTML partial for HTMX requests, JSON GameTimeInfo otherwise.
    """
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

    # Return HTML for HTMX requests, JSON for API clients
    if request.headers.get("HX-Request"):
        updated_active_expeditions = db.query(Expedition).filter(Expedition.result == "in_progress").all()
        player = db.query(Player).first()
        treasury_gold = player.treasury if player else 0
        return templates.TemplateResponse(
            "partials/active_expeditions.html",
            {
                "request": request,
                "active_expeditions": updated_active_expeditions,
                "game_time": game_time,
                "treasury_gold": treasury_gold
            }
        )

    return GameTimeInfo(
        current_day=game_time.current_day,
        day_started_at=game_time.day_started_at,
        last_updated=game_time.last_updated
    )


@router.get("/time/", response_model=GameTimeInfo)
def get_game_time(db: Session = Depends(get_db)):
    """Get current game time"""
    game_time = db.query(GameTime).first()
    if not game_time:
        raise HTTPException(status_code=404, detail="Game time not initialized")
    return game_time

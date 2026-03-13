from fastapi import APIRouter, HTTPException, Depends, Form, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request
from typing import List, Optional

from app.database import get_db
from app.models import Adventurer, Player
from app.schemas import AdventurerOut, AdventurerCreate, LevelUpResult
from app.progression import (
    calculate_xp_for_next_level, check_for_level_up,
    calculate_hp_gain, get_class_level_bonuses
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def add_progression_data(adventurer):
    next_level_xp = calculate_xp_for_next_level(adventurer.level)

    if next_level_xp:
        current_level_xp = calculate_xp_for_next_level(adventurer.level - 1) or 0
        xp_for_current_level = adventurer.xp - current_level_xp
        xp_needed_for_next = next_level_xp - current_level_xp
        progress = (xp_for_current_level / xp_needed_for_next) * 100 if xp_needed_for_next > 0 else 100
    else:
        progress = 100

    adventurer.next_level_xp = next_level_xp
    adventurer.xp_progress = min(100, max(0, progress))
    return adventurer


@router.post("/adventurers/", response_model=AdventurerOut)
def create_adventurer(adventurer: AdventurerCreate, db: Session = Depends(get_db)):
    adv = Adventurer(
        name=adventurer.name,
        adventurer_class=adventurer.adventurer_class,
        level=adventurer.level,
        hp_max=adventurer.hp_max,
        hp_current=adventurer.hp_max,
        xp=0,
        gold=0,
        is_available=True,
    )
    db.add(adv)
    db.commit()
    db.refresh(adv)
    return add_progression_data(adv)


@router.get("/adventurers/", response_model=list[AdventurerOut])
def list_adventurers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    adventurers = db.query(Adventurer).offset(skip).limit(limit).all()
    return [add_progression_data(adv) for adv in adventurers]


@router.get("/adventurers/{adventurer_id}", response_model=AdventurerOut)
def get_adventurer(adventurer_id: int, db: Session = Depends(get_db)):
    """Get a specific adventurer by ID"""
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    return add_progression_data(adventurer)


@router.post("/adventurers/{adventurer_id}/level-up", response_model=LevelUpResult)
def level_up_adventurer(adventurer_id: int, db: Session = Depends(get_db)):
    """Level up an adventurer if they have enough XP"""
    adventurer = db.query(Adventurer).filter(Adventurer.id == adventurer_id).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    if adventurer.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot level up an adventurer while they are on an expedition"
        )

    if not check_for_level_up(adventurer.level, adventurer.xp):
        raise HTTPException(status_code=400, detail="Not enough XP to level up")

    old_level = adventurer.level
    adventurer.level += 1

    hp_gain = calculate_hp_gain(adventurer.adventurer_class, old_level)
    adventurer.hp_max += hp_gain
    adventurer.hp_current += hp_gain

    class_bonuses = get_class_level_bonuses(adventurer.adventurer_class, adventurer.level)

    db.commit()
    db.refresh(adventurer)

    next_level_xp = calculate_xp_for_next_level(adventurer.level)

    return {
        "old_level": old_level,
        "new_level": adventurer.level,
        "hp_gained": hp_gain,
        "next_level_xp": next_level_xp,
        "class_bonuses": class_bonuses
    }


# --- Frontend Routes ---

@router.get("/adventurers", response_class=HTMLResponse)
def adventurers_page(request: Request, db: Session = Depends(get_db)):
    """Render the adventurers page"""
    adventurers = db.query(Adventurer).all()

    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    return templates.TemplateResponse(
        "adventurers.html",
        {"request": request, "adventurers": adventurers, "treasury_gold": treasury_gold}
    )


@router.get("/adventurers/create-form", response_class=HTMLResponse)
def adventurer_create_form(request: Request, db: Session = Depends(get_db)):
    """Return the adventurer creation form"""
    treasury_gold = 0
    player = db.query(Player).first()
    if player:
        treasury_gold = player.treasury

    return templates.TemplateResponse(
        "partials/adventurer_form.html",
        {"request": request, "treasury_gold": treasury_gold}
    )

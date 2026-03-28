from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_keep
from app.database import get_db
from app.models import Adventurer, Expedition, Keep, Party
from app.progression import calculate_hp_gain, calculate_xp_for_next_level, check_for_level_up, get_class_level_bonuses
from app.schemas import AdventurerCreate, AdventurerOut, LevelUpResult

router = APIRouter()


def _get_active_expedition_hps(keep: Keep, db: Session) -> dict[str, int]:
    """Pre-calculate current HP for all adventurers on active expeditions."""
    from app.routes.expeditions import _build_active_summary
    active_expeditions = db.query(Expedition).join(Party, Expedition.party_id == Party.id).filter(
        Party.keep_id == keep.id,
        Expedition.result.in_(["in_progress", "awaiting_choice"]),
    ).all()

    current_hps = {} # (adventurer_name) -> hp
    for exp in active_expeditions:
        summary = _build_active_summary(exp, exp.party, keep)
        for mr in summary.get("member_results", []):
            current_hps[mr["name"]] = mr["hp_current"]
    return current_hps


def add_progression_data(adventurer, current_hps=None):
    from app.class_config import get_class_config, get_combat_hd, get_thac0, get_to_hit_bonus

    if current_hps and adventurer.name in current_hps:
        adventurer.hp_current = current_hps[adventurer.name]

    next_level_xp = calculate_xp_for_next_level(adventurer.level, adventurer.adventurer_class)

    if next_level_xp:
        current_level_xp = calculate_xp_for_next_level(adventurer.level - 1, adventurer.adventurer_class) or 0
        xp_for_current_level = adventurer.xp - current_level_xp
        xp_needed_for_next = next_level_xp - current_level_xp
        progress = (xp_for_current_level / xp_needed_for_next) * 100 if xp_needed_for_next > 0 else 100
    else:
        current_level_xp = calculate_xp_for_next_level(adventurer.level - 1, adventurer.adventurer_class) or 0
        progress = 100

    adventurer.next_level_xp = next_level_xp
    adventurer.current_level_xp = current_level_xp
    adventurer.xp_progress = min(100, max(0, progress))

    # Combat stats
    cls = adventurer.adventurer_class.value if hasattr(adventurer.adventurer_class, 'value') else adventurer.adventurer_class
    adventurer.thac0 = get_thac0(cls, adventurer.level)
    adventurer.hit_dice = get_combat_hd(cls, adventurer.level)
    adventurer.to_hit_bonus = get_to_hit_bonus(cls)

    # Class ability summary
    cfg = get_class_config(cls)
    abilities = cfg.get("abilities", {})
    if abilities:
        ability_name = next(iter(abilities))
        adventurer.class_ability = abilities[ability_name].get("description", "")
    else:
        adventurer.class_ability = None

    # Party name
    adventurer.party_name = adventurer.parties[0].name if adventurer.parties else None

    return adventurer


@router.post("/adventurers/", response_model=AdventurerOut)
def create_adventurer(
    adventurer: AdventurerCreate,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    adv = Adventurer(
        keep_id=keep.id,
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
def list_adventurers(
    skip: int = 0,
    limit: int = 100,
    include_all: bool = False,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    query = db.query(Adventurer).filter(Adventurer.keep_id == keep.id)
    if not include_all:
        query = query.filter(
            Adventurer.is_dead == False,
            Adventurer.is_bankrupt == False,
        )
    adventurers = query.offset(skip).limit(limit).all()
    current_hps = _get_active_expedition_hps(keep, db)
    return [add_progression_data(adv, current_hps) for adv in adventurers]


@router.get("/adventurers/graveyard", response_model=list[AdventurerOut])
def get_graveyard(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """List all dead adventurers"""
    dead = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_dead == True,
    ).all()
    return [add_progression_data(a) for a in dead]


@router.get("/adventurers/debtors-prison", response_model=list[AdventurerOut])
def get_debtors_prison(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """List all bankrupt adventurers"""
    bankrupt = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.is_bankrupt == True,
    ).all()
    return [add_progression_data(a) for a in bankrupt]


@router.get("/adventurers/by-name/{name}", response_model=AdventurerOut)
def get_adventurer_by_name(
    name: str,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get a specific adventurer by name (including dead/bankrupt)."""
    adventurer = db.query(Adventurer).filter(
        Adventurer.keep_id == keep.id,
        Adventurer.name == name,
    ).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    current_hps = _get_active_expedition_hps(keep, db)
    return add_progression_data(adventurer, current_hps)


@router.get("/adventurers/{adventurer_id}", response_model=AdventurerOut)
def get_adventurer(
    adventurer_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Get a specific adventurer by ID"""
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == adventurer_id,
        Adventurer.keep_id == keep.id,
    ).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")
    current_hps = _get_active_expedition_hps(keep, db)
    return add_progression_data(adventurer, current_hps)


@router.post("/adventurers/{adventurer_id}/level-up", response_model=LevelUpResult)
def level_up_adventurer(
    adventurer_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Level up an adventurer if they have enough XP"""
    adventurer = db.query(Adventurer).filter(
        Adventurer.id == adventurer_id,
        Adventurer.keep_id == keep.id,
    ).first()
    if not adventurer:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    if adventurer.on_expedition:
        raise HTTPException(
            status_code=400,
            detail="Cannot level up an adventurer while they are on an expedition"
        )

    if not check_for_level_up(adventurer.level, adventurer.xp, adventurer.adventurer_class):
        raise HTTPException(status_code=400, detail="Not enough XP to level up")

    old_level = adventurer.level
    adventurer.level += 1

    hp_gain = calculate_hp_gain(adventurer.adventurer_class, old_level)
    adventurer.hp_max += hp_gain
    adventurer.hp_current += hp_gain

    class_bonuses = get_class_level_bonuses(adventurer.adventurer_class, adventurer.level)

    db.commit()
    db.refresh(adventurer)

    next_level_xp = calculate_xp_for_next_level(adventurer.level, adventurer.adventurer_class)

    return {
        "old_level": old_level,
        "new_level": adventurer.level,
        "hp_gained": hp_gain,
        "next_level_xp": next_level_xp,
        "class_bonuses": class_bonuses
    }

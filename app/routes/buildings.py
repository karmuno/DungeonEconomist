from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Keep, Building, Adventurer
from app.auth import get_current_keep
from app.buildings import (
    BUILDING_TYPES, BUILDING_CONFIG, get_building_name, get_upgrade_cost,
    get_max_assigned, get_min_level_for_assignment, get_max_building_level,
    get_building_class,
)

router = APIRouter(prefix="/buildings", tags=["buildings"])


def _building_response(building: Building) -> dict:
    """Format a building for API response."""
    btype = building.building_type
    config = BUILDING_CONFIG.get(btype, {})
    return {
        "id": building.id,
        "building_type": btype,
        "name": get_building_name(btype, building.level),
        "level": building.level,
        "max_level": get_max_building_level(btype),
        "adventurer_class": get_building_class(btype),
        "description": config.get("description", ""),
        "assigned_bonus_desc": config.get("assigned_bonus_desc", ""),
        "max_assigned": get_max_assigned(btype, building.level),
        "min_adventurer_level": get_min_level_for_assignment(btype, building.level),
        "assigned_adventurers": [
            {
                "id": a.id,
                "name": a.name,
                "adventurer_class": a.adventurer_class.value,
                "level": a.level,
            }
            for a in building.assigned_adventurers
        ],
        "upgrade_cost": get_upgrade_cost(btype, building.level + 1) if building.level < get_max_building_level(btype) else None,
        "next_name": get_building_name(btype, building.level + 1) if building.level < get_max_building_level(btype) else None,
    }


@router.get("/")
def list_buildings(keep: Keep = Depends(get_current_keep), db: Session = Depends(get_db)):
    """List all buildings (built and available to buy)."""
    built = db.query(Building).filter(Building.keep_id == keep.id).all()
    built_types = {b.building_type for b in built}

    result = []
    for b in built:
        result.append(_building_response(b))

    # Show unbuilt buildings as purchasable
    for btype in BUILDING_TYPES:
        if btype not in built_types:
            config = BUILDING_CONFIG.get(btype, {})
            result.append({
                "id": None,
                "building_type": btype,
                "name": get_building_name(btype, 1),
                "level": 0,
                "max_level": get_max_building_level(btype),
                "adventurer_class": get_building_class(btype),
                "description": config.get("description", ""),
                "assigned_bonus_desc": config.get("assigned_bonus_desc", ""),
                "max_assigned": 0,
                "min_adventurer_level": get_min_level_for_assignment(btype, 1),
                "assigned_adventurers": [],
                "buy_cost": get_upgrade_cost(btype, 1),
                "upgrade_cost": None,
                "next_name": None,
            })

    return result


class BuildingAction(BaseModel):
    building_type: str


@router.post("/buy")
def buy_building(
    data: BuildingAction,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Buy a new building (level 1)."""
    if data.building_type not in BUILDING_TYPES:
        raise HTTPException(status_code=400, detail="Invalid building type")

    existing = db.query(Building).filter(
        Building.keep_id == keep.id,
        Building.building_type == data.building_type,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Building already exists")

    cost = get_upgrade_cost(data.building_type, 1)
    cost_copper = cost * 100
    if keep.treasury_total_copper() < cost_copper:
        raise HTTPException(status_code=400, detail=f"Not enough gold. Need {cost}gp")

    # Deduct cost
    total = keep.treasury_total_copper() - cost_copper
    keep.treasury_gold = total // 100
    keep.treasury_silver = (total % 100) // 10
    keep.treasury_copper = total % 10

    building = Building(keep_id=keep.id, building_type=data.building_type, level=1)
    db.add(building)
    db.commit()
    db.refresh(building)

    return _building_response(building)


@router.post("/{building_id}/upgrade")
def upgrade_building(
    building_id: int,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Upgrade a building to the next level."""
    building = db.query(Building).filter(
        Building.id == building_id,
        Building.keep_id == keep.id,
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    max_level = get_max_building_level(building.building_type)
    if building.level >= max_level:
        raise HTTPException(status_code=400, detail="Building is already at max level")

    cost = get_upgrade_cost(building.building_type, building.level + 1)
    cost_copper = cost * 100
    if keep.treasury_total_copper() < cost_copper:
        raise HTTPException(status_code=400, detail=f"Not enough gold. Need {cost}gp")

    total = keep.treasury_total_copper() - cost_copper
    keep.treasury_gold = total // 100
    keep.treasury_silver = (total % 100) // 10
    keep.treasury_copper = total % 10

    building.level += 1
    db.commit()
    db.refresh(building)

    return _building_response(building)


class AssignAction(BaseModel):
    adventurer_id: int


@router.post("/{building_id}/assign")
def assign_adventurer(
    building_id: int,
    data: AssignAction,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Assign an adventurer to a building."""
    building = db.query(Building).filter(
        Building.id == building_id,
        Building.keep_id == keep.id,
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    adv = db.query(Adventurer).filter(
        Adventurer.id == data.adventurer_id,
        Adventurer.keep_id == keep.id,
    ).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    # Validations
    required_class = get_building_class(building.building_type)
    if adv.adventurer_class.value != required_class:
        raise HTTPException(status_code=400, detail=f"Only {required_class}s can be assigned here")

    min_level = get_min_level_for_assignment(building.building_type, building.level)
    if adv.level < min_level:
        raise HTTPException(status_code=400, detail=f"Adventurer must be at least level {min_level}")

    if adv.is_dead or adv.is_bankrupt or adv.on_expedition or adv.is_assigned:
        raise HTTPException(status_code=400, detail="Adventurer is not available for assignment")

    max_slots = get_max_assigned(building.building_type, building.level)
    if len(building.assigned_adventurers) >= max_slots:
        raise HTTPException(status_code=400, detail=f"Building is full ({max_slots} slots)")

    # Assign
    building.assigned_adventurers.append(adv)
    adv.is_assigned = True
    adv.is_available = False
    # Remove from any parties
    adv.parties = []
    db.commit()

    return _building_response(building)


@router.post("/{building_id}/unassign")
def unassign_adventurer(
    building_id: int,
    data: AssignAction,
    keep: Keep = Depends(get_current_keep),
    db: Session = Depends(get_db),
):
    """Remove an adventurer from a building."""
    building = db.query(Building).filter(
        Building.id == building_id,
        Building.keep_id == keep.id,
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    adv = db.query(Adventurer).filter(
        Adventurer.id == data.adventurer_id,
        Adventurer.keep_id == keep.id,
    ).first()
    if not adv:
        raise HTTPException(status_code=404, detail="Adventurer not found")

    if adv not in building.assigned_adventurers:
        raise HTTPException(status_code=400, detail="Adventurer is not assigned to this building")

    building.assigned_adventurers.remove(adv)
    adv.is_assigned = False
    adv.is_available = True
    db.commit()

    return _building_response(building)

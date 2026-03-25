from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_keep
from app.buildings import (
    BUILDING_CONFIG,
    BUILDING_TYPES,
    can_assign_new,
    get_all_building_bonuses,
    get_allowed_classes,
    get_building_class,
    get_building_name,
    get_max_assigned,
    get_max_building_level,
    get_min_level_for_assignment,
    get_tier_slots,
    get_upgrade_cost,
    has_recruitment_bonus,
)
from app.database import get_db
from app.models import Adventurer, Building, Keep

router = APIRouter(prefix="/buildings", tags=["buildings"])


def _building_response(building: Building) -> dict:
    """Format a building for API response."""
    btype = building.building_type
    config = BUILDING_CONFIG.get(btype, {})
    assigned_count = len(building.assigned_adventurers)
    cls = get_building_class(btype)
    allowed = get_allowed_classes(btype)

    # Compute current effects from all unlocked tiers
    effects = []
    if has_recruitment_bonus(btype):
        effects.append(f"2x {cls} recruitment")
    if assigned_count > 0:
        bonuses = get_all_building_bonuses(btype, building.level)
        if "healing_per_assigned" in bonuses:
            effects.append(f"+{assigned_count * bonuses['healing_per_assigned']} HP/day healing")
        if "to_hit_per_assigned" in bonuses:
            effects.append(f"+{assigned_count * bonuses['to_hit_per_assigned']} to-hit")
        if "damage_per_assigned" in bonuses:
            effects.append(f"+{assigned_count * bonuses['damage_per_assigned']} damage")
        if "monster_morale_penalty" in bonuses:
            effects.append(f"Monster morale {bonuses['monster_morale_penalty']}")
        if "healing_potion_chance_per_cleric" in bonuses:
            effects.append("Healing Potion crafting")
        if "resurrect_highest_dead" in bonuses:
            effects.append("Resurrection on return")
        if "magic_item_discovery_per_assigned" in bonuses:
            pct = assigned_count * bonuses['magic_item_discovery_per_assigned'] * 100
            effects.append(f"+{pct:.0f}% magic item discovery")
        if "scroll_craft_chance_per_mu" in bonuses:
            effects.append("Scroll crafting")
        if "craft_artifact_cost" in bonuses:
            effects.append(f"Artifact crafting ({bonuses['craft_artifact_cost']}gp)")
        if "craft_weapon_slot" in bonuses or "craft_armor_slot" in bonuses:
            effects.append("Weapon/Armor crafting")
        if "masterwork_chance" in bonuses:
            effects.append(f"Masterwork chance ({bonuses['masterwork_chance'] * 100:.0f}%)")

    return {
        "id": building.id,
        "building_type": btype,
        "name": get_building_name(btype, building.level),
        "level": building.level,
        "max_level": get_max_building_level(btype),
        "adventurer_class": cls,
        "allowed_classes": allowed,
        "description": config.get("description", ""),
        "assigned_bonus_desc": config.get("assigned_bonus_desc", ""),
        "effects": effects,
        "max_assigned": get_max_assigned(btype, building.level),
        "tier_slots": [
            {"tier": t, "slots": s, "min_level": ml}
            for t, s, ml in get_tier_slots(btype, building.level)
        ],
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
        if b.building_type not in BUILDING_TYPES:
            continue  # Skip legacy buildings from old config
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

    # Validations — use allowed_classes for cross-class support
    allowed = get_allowed_classes(building.building_type)
    if adv.adventurer_class.value not in allowed:
        allowed_str = ", ".join(allowed)
        raise HTTPException(status_code=400, detail=f"Only {allowed_str} can be assigned here")

    tier_slots = get_tier_slots(building.building_type, building.level)
    min_entry_level = min(ml for _, _, ml in tier_slots) if tier_slots else 1
    if adv.level < min_entry_level:
        raise HTTPException(status_code=400, detail=f"Adventurer must be at least level {min_entry_level}")

    if adv.is_dead or adv.is_bankrupt or adv.on_expedition or adv.is_assigned:
        raise HTTPException(status_code=400, detail="Adventurer is not available for assignment")

    current_levels = [a.level for a in building.assigned_adventurers]
    if not can_assign_new(building.building_type, building.level, current_levels, adv.level):
        raise HTTPException(status_code=400, detail="No slot available for this adventurer's level")

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

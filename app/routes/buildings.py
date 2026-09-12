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
    get_xp_bonus,
)
from app.database import get_db
from app.models import Adventurer, Building, Keep
from app.player_events import EventType, log_player_event

router = APIRouter(prefix="/buildings", tags=["buildings"])


def _tier_min_level(btype: str, key: str) -> int:
    """The adventurer level a staff member needs before `key` counts: the min level of the tier granting it."""
    config = BUILDING_CONFIG.get(btype, {})
    levels = config.get("min_adventurer_level", [2, 5, 8])
    for tier, bonuses in config.get("level_bonuses", {}).items():
        if key in bonuses:
            return levels[min(int(tier) - 1, len(levels) - 1)]
    return 1


def _staff_for(building: Building | None, btype: str, key: str) -> int:
    """How many assigned adventurers qualify for the tier that grants `key`."""
    if building is None:
        return 0
    need = _tier_min_level(btype, key)
    return sum(1 for a in building.assigned_adventurers if a.level >= need)


def _pct(v: float) -> str:
    return f"{v * 100:.0f}%"


# Stat renderers: (bonus key, row label, rate formatter, total formatter).
# The rate is the per-unit number from config; the total is what the building
# delivers right now given who is assigned (None when nobody qualifies).
_STAT_RENDERERS = [
    ("healing_per_assigned", "Healing",
     lambda v: f"+{v} HP/day each", lambda v, n: f"+{v * n} HP/day"),
    ("to_hit_per_assigned", "To-hit",
     lambda v: f"+{v} each", lambda v, n: f"+{v * n}"),
    ("damage_per_assigned", "Damage",
     lambda v: f"+{v} each", lambda v, n: f"+{v * n}"),
    ("monster_morale_penalty", "Monster morale",
     lambda v: f"−{abs(v)}", lambda v, n: f"−{abs(v)}"),
    ("healing_potion_chance_per_cleric", "Potion craft",
     lambda v: f"{_pct(v)} each", lambda v, n: _pct(v * n)),
    ("resurrect_highest_dead", "Resurrection",
     lambda v: "On return", lambda v, n: "On return"),
    ("magic_item_discovery_per_assigned", "Item find",
     lambda v: f"+{_pct(v)} each", lambda v, n: f"+{_pct(v * n)}"),
    ("scroll_craft_chance_per_mu", "Scroll craft",
     lambda v: f"{_pct(v)} each", lambda v, n: _pct(v * n)),
    ("craft_artifact_cost", "Artifacts",
     lambda v: f"{v}gp", lambda v, n: f"{v}gp"),
    ("craft_weapon_slot", "Crafting",
     lambda v: "Weapon/Armor each", lambda v, n: f"{n} slot{'' if n == 1 else 's'}"),
    ("masterwork_chance", "Masterwork",
     lambda v: _pct(v), lambda v, n: _pct(v)),
]


def _stat_lines(btype: str, level: int, building: Building | None = None) -> list[dict]:
    """Every effect the building has, one row each: the rate from config and, for a
    standing building, the total it delivers now. Slots and XP come last."""
    if level <= 0:
        return []
    bonuses = get_all_building_bonuses(btype, level)
    lines = []
    for key, label, rate_fmt, total_fmt in _STAT_RENDERERS:
        if key not in bonuses:
            continue
        v = bonuses[key]
        n = _staff_for(building, btype, key)
        total = total_fmt(v, n) if (building is not None and n > 0) else None
        lines.append({"label": label, "value": rate_fmt(v), "total": total})
    tier_slots = get_tier_slots(btype, level)
    if tier_slots:
        slot_str = ", ".join(f"{s} · Lv {ml}+" for _, s, ml in tier_slots)
        free = None
        if building is not None:
            free = get_max_assigned(btype, level) - len(building.assigned_adventurers)
            free = f"{free} free"
        lines.append({"label": "Slots", "value": slot_str, "total": free})
    xp = get_xp_bonus(btype)
    if xp:
        rate = f"+{_pct(xp)}"
        lines.append({"label": "XP", "value": rate, "total": rate if building is not None else None})
    return lines


_CLASS_PLURALS = {
    "Fighter": "Fighters",
    "Cleric": "Clerics",
    "Magic-User": "Magic-Users",
    "Elf": "Elves",
    "Dwarf": "Dwarves",
    "Halfling": "Halflings",
}


def staffed_effects(building: Building) -> list[str]:
    """Dashboard copy for what the assigned staff deliver now (Cody, 2026-09-12). Empty until
    someone is assigned."""
    btype = building.building_type
    lines = _stat_lines(btype, min(building.level, 1), building)
    totals = {line["label"]: line["total"] for line in lines}
    effects = []
    if totals.get("Healing"):
        effects.append(f"{totals['Healing']} while healing")
    if totals.get("Item find"):
        effects.append(f"{totals['Item find']} chance to find items")
    if totals.get("To-hit"):
        effects.append(f"{totals['To-hit']} to-hit in combat")
    bonuses = get_all_building_bonuses(btype, building.level)
    smiths = _staff_for(building, btype, "craft_weapon_slot") if "craft_weapon_slot" in bonuses else 0
    if smiths:
        chance = bonuses.get("craft_chance", 0.10)
        effects.append(f"+{_pct(chance * smiths)} chance to forge magic armaments")
    return effects


def standing_effects(building: Building) -> list[str]:
    """What the building grants just by standing: its XP line."""
    btype = building.building_type
    xp = get_xp_bonus(btype)
    if not xp:
        return []
    classes = "/".join(_CLASS_PLURALS.get(c, c) for c in get_allowed_classes(btype))
    return [f"+{_pct(xp)} XP {classes}"]


def building_effects(building: Building) -> list[str]:
    """Everything the building is doing now: staffed effects first, standing last."""
    return staffed_effects(building) + standing_effects(building)


def _building_response(building: Building) -> dict:
    """Format a building for API response."""
    btype = building.building_type
    config = BUILDING_CONFIG.get(btype, {})
    assigned_count = len(building.assigned_adventurers)
    cls = get_building_class(btype)
    allowed = get_allowed_classes(btype)

    effects = building_effects(building)

    shown_level = min(building.level, 1)
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
        # Tier II+ UI is hidden for the MVP (tier-slot bonus math is not trustworthy yet):
        # the Village only ever shows Tier I slots, Tier I stats, and no upgrade offer.
        "tier_slots": [
            {"tier": t, "slots": s, "min_level": ml}
            for t, s, ml in get_tier_slots(btype, shown_level)
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
        "upgrade_cost": None,
        "next_name": None,
        "slots_total": get_max_assigned(btype, shown_level),
        "slots_free": get_max_assigned(btype, shown_level) - assigned_count,
        "current_stats": _stat_lines(btype, shown_level, building),
        "next_stats": None,
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
                "next_name": get_building_name(btype, 1),
                "allowed_classes": get_allowed_classes(btype),
                "tier_slots": [],
                "current_stats": [],
                "next_stats": _stat_lines(btype, 1),
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
    log_player_event(db, EventType.BUILDING_PURCHASED, keep.account_id, keep.id, {
        "building_type": data.building_type, "level": 1, "cost_gp": cost,
    })
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
    log_player_event(db, EventType.BUILDING_PURCHASED, keep.account_id, keep.id, {
        "building_type": building.building_type, "level": building.level, "cost_gp": cost,
    })
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
    log_player_event(db, EventType.ADVENTURER_ASSIGNED_TO_BUILDING, keep.account_id, keep.id, {
        "adventurer_name": adv.name,
        "class": adv.adventurer_class.value,
        "level": adv.level,
        "building_type": building.building_type,
        "building_level": building.level,
    })
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

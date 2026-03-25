"""Building configuration and bonus calculations."""

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "buildings.json"

with open(_DATA_PATH) as f:
    BUILDING_CONFIG = json.load(f)

BUILDING_TYPES = list(BUILDING_CONFIG.keys())


def get_building_name(building_type: str, level: int) -> str:
    """Get the display name for a building at a given level."""
    config = BUILDING_CONFIG.get(building_type, {})
    names = config.get("names", ["Unknown"])
    idx = min(level - 1, len(names) - 1)
    return names[idx]


def get_upgrade_cost(building_type: str, target_level: int) -> int:
    """Get the cost in gold to upgrade/buy to a given level (1-indexed)."""
    config = BUILDING_CONFIG.get(building_type, {})
    costs = config.get("costs", [500, 2500, 12500])
    idx = min(target_level - 1, len(costs) - 1)
    return costs[idx]


def get_min_level_for_assignment(building_type: str, building_level: int) -> int:
    """Minimum adventurer level to be assigned at this building level.

    Since tiers are additive, returns the min level for the *highest* unlocked tier.
    For the full tier breakdown, use get_tier_slots().
    """
    config = BUILDING_CONFIG.get(building_type, {})
    levels = config.get("min_adventurer_level", [2, 5, 8])
    idx = min(building_level - 1, len(levels) - 1)
    return levels[idx]


def get_tier_slots(building_type: str, building_level: int) -> list[tuple[int, int, int]]:
    """Return a list of (tier, slot_count, min_adventurer_level) for all unlocked tiers.

    Tiers are additive: a Level 2 building has both Tier 1 and Tier 2 slots.
    """
    config = BUILDING_CONFIG.get(building_type, {})
    max_assigned = config.get("max_assigned", [3, 6, 9])
    min_levels = config.get("min_adventurer_level", [2, 5, 8])
    tiers = []
    for tier in range(min(building_level, len(max_assigned))):
        tiers.append((tier + 1, max_assigned[tier], min_levels[tier]))
    return tiers


def get_max_assigned(building_type: str, building_level: int) -> int:
    """Total assignable slots at this building level (sum across all unlocked tiers)."""
    return sum(slots for _, slots, _ in get_tier_slots(building_type, building_level))


def get_retire_level(building_type: str) -> int:
    """Minimum level for an adventurer to retire into this building."""
    config = BUILDING_CONFIG.get(building_type, {})
    return config.get("retire_level", 9)


def get_max_building_level(building_type: str) -> int:
    """Max level this building can reach (driven by length of names array)."""
    config = BUILDING_CONFIG.get(building_type, {})
    return len(config.get("names", ["Unknown"]))


def get_building_class(building_type: str) -> str:
    """Get the primary adventurer class associated with this building."""
    config = BUILDING_CONFIG.get(building_type, {})
    return config.get("class", "Fighter")


def get_allowed_classes(building_type: str) -> list[str]:
    """Get all adventurer classes that can be assigned to this building."""
    config = BUILDING_CONFIG.get(building_type, {})
    return config.get("allowed_classes", [config.get("class", "Fighter")])


def get_building_bonuses(building_type: str, building_level: int) -> dict:
    """Get the passive bonuses for a building at a given level."""
    config = BUILDING_CONFIG.get(building_type, {})
    bonuses = config.get("level_bonuses", {})
    return bonuses.get(str(building_level), {})


def get_all_building_bonuses(building_type: str, building_level: int) -> dict:
    """Get merged bonuses across all unlocked tiers (since tiers are additive)."""
    config = BUILDING_CONFIG.get(building_type, {})
    all_bonuses = config.get("level_bonuses", {})
    merged = {}
    for tier in range(1, building_level + 1):
        tier_bonuses = all_bonuses.get(str(tier), {})
        merged.update(tier_bonuses)
    return merged


def has_recruitment_bonus(building_type: str) -> bool:
    """Whether this building doubles recruitment chance for its class."""
    config = BUILDING_CONFIG.get(building_type, {})
    return config.get("recruitment_bonus", False)


def can_assign_class(building_type: str, adventurer_class: str) -> bool:
    """Check if an adventurer class can be assigned to this building type."""
    return adventurer_class in get_allowed_classes(building_type)


def can_assign_at_level(building_type: str, building_level: int, adventurer_level: int) -> bool:
    """Check if an adventurer of the given level can fill any tier slot."""
    return any(adventurer_level >= min_lvl for _, _, min_lvl in get_tier_slots(building_type, building_level))


def can_assign_new(
    building_type: str,
    building_level: int,
    current_levels: list[int],
    new_level: int,
) -> bool:
    """Return True if new_level can be assigned given the current occupant levels.

    Tiers are greedy/bottom-up: each adventurer fills the lowest qualifying tier
    that still has capacity.  This means a high-level adventurer only consumes a
    high-tier slot when all lower-tier slots it qualifies for are already full,
    ensuring lower-level adventurers are never locked out by higher-level ones
    that could have gone into an upper tier.
    """
    tiers = get_tier_slots(building_type, building_level)
    remaining = {tier: slots for tier, slots, _ in tiers}

    for level in sorted(current_levels + [new_level]):
        placed = False
        for tier, _, min_lvl in tiers:
            if level >= min_lvl and remaining[tier] > 0:
                remaining[tier] -= 1
                placed = True
                break
        if not placed:
            return False
    return True


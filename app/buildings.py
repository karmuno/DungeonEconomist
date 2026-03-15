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


def get_min_level_for_assignment(building_type: str, building_level: int) -> int:
    """Minimum adventurer level to be assigned at this building level."""
    config = BUILDING_CONFIG.get(building_type, {})
    levels = config.get("min_adventurer_level", [2, 5, 8])
    idx = min(building_level - 1, len(levels) - 1)
    return levels[idx]


def get_max_assigned(building_type: str, building_level: int) -> int:
    """Max adventurers assignable at this building level."""
    config = BUILDING_CONFIG.get(building_type, {})
    caps = config.get("max_assigned", [1, 2, 3])
    idx = min(building_level - 1, len(caps) - 1)
    return caps[idx]


def get_retire_level(building_type: str) -> int:
    """Minimum level for an adventurer to retire into this building."""
    config = BUILDING_CONFIG.get(building_type, {})
    return config.get("retire_level", 9)


def get_building_bonuses(building_type: str, building_level: int) -> dict:
    """Get the passive bonuses for a building at a given level."""
    config = BUILDING_CONFIG.get(building_type, {})
    bonuses = config.get("bonuses", {})
    return bonuses.get(str(building_level), {})


def get_max_building_level(building_type: str) -> int:
    """Max level this building can reach (driven by length of names array)."""
    config = BUILDING_CONFIG.get(building_type, {})
    return len(config.get("names", ["Unknown"]))


def get_building_class(building_type: str) -> str:
    """Get the adventurer class associated with this building."""
    config = BUILDING_CONFIG.get(building_type, {})
    return config.get("class", "Fighter")

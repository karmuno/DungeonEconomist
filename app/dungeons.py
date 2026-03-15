"""Dungeon name generation and dungeon data."""

import json
import random
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "dungeons.json"

with open(_DATA_PATH) as f:
    _DUNGEON_DATA = json.load(f)

_PREFIXES = _DUNGEON_DATA["name_prefixes"]
_SUFFIXES = _DUNGEON_DATA["name_suffixes"]
_MIDDLES = _DUNGEON_DATA["name_middle"]
DUNGEON_LEVELS = _DUNGEON_DATA["dungeon_levels"]
DUNGEON_LEVEL_NAMES = [lvl["name"] for lvl in DUNGEON_LEVELS]


def generate_dungeon_name() -> str:
    """Generate a unique dungeon name. ~42,000 possible combinations."""
    prefix = random.choice(_PREFIXES)
    suffix = random.choice(_SUFFIXES)

    # 60% chance to include a middle phrase for variety
    if random.random() < 0.6:
        middle = random.choice(_MIDDLES)
        return f"{prefix} {suffix} {middle}"
    return f"{prefix} {suffix}"


def get_level_duration(level: int) -> int:
    """Get the expedition duration in days for a given dungeon level (1-indexed)."""
    idx = level - 1
    if 0 <= idx < len(DUNGEON_LEVELS):
        return DUNGEON_LEVELS[idx]["duration_days"]
    return 7  # fallback

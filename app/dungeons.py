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
DUNGEON_LEVEL_NAMES = _DUNGEON_DATA["dungeon_level_names"]

# 50 prefixes × 40 suffixes = 2,000 two-part names
# 50 prefixes × 40 suffixes × 20 middles = 40,000 three-part names
# Combined: well over 10,000


def generate_dungeon_name() -> str:
    """Generate a unique dungeon name. ~42,000 possible combinations."""
    prefix = random.choice(_PREFIXES)
    suffix = random.choice(_SUFFIXES)

    # 60% chance to include a middle phrase for variety
    if random.random() < 0.6:
        middle = random.choice(_MIDDLES)
        return f"{prefix} {suffix} {middle}"
    return f"{prefix} {suffix}"

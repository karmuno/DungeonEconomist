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
_LEVEL_ADJECTIVES = _DUNGEON_DATA["level_adjectives"]
_LEVEL_PLACES = _DUNGEON_DATA["level_places"]
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


def generate_level_names(count: int) -> list[str]:
    """Generate `count` unique dungeon level names like 'The Echoing Halls'."""
    used: set[str] = set()
    names: list[str] = []
    adjectives = _LEVEL_ADJECTIVES[:]
    places = _LEVEL_PLACES[:]
    random.shuffle(adjectives)
    random.shuffle(places)
    attempts = 0
    while len(names) < count and attempts < 200:
        adj = random.choice(adjectives)
        place = random.choice(places)
        name = f"The {adj} {place}"
        if name not in used:
            used.add(name)
            names.append(name)
        attempts += 1
    # Fallback if pool exhausted
    while len(names) < count:
        names.append(DUNGEON_LEVEL_NAMES[len(names) % len(DUNGEON_LEVEL_NAMES)])
    return names


def get_level_duration(level: int) -> int:
    """Get the expedition duration in days for a given dungeon level (1-indexed)."""
    idx = level - 1
    if 0 <= idx < len(DUNGEON_LEVELS):
        return DUNGEON_LEVELS[idx]["duration_days"]
    return 7  # fallback

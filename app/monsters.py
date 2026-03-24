"""Monster data from JSON config."""

import json
import random
import re
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "monsters.json"

with open(_DATA_PATH) as f:
    MONSTER_CONFIG = json.load(f)

_MONSTERS = MONSTER_CONFIG["monsters"]
_ENCOUNTER_TABLES = MONSTER_CONFIG["encounter_tables"]


def _roll_dice(expr: str) -> int:
    """Roll dice from an expression like '2d6', '1d10-1', '3d8+2', or a plain int."""
    if not expr:
        return 0
    expr = str(expr).strip()
    match = re.match(r'(\d+)d(\d+)([+-]\d+)?', expr)
    if not match:
        return int(expr)
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    total = sum(random.randint(1, sides) for _ in range(count)) + modifier
    return max(1, total)


def get_random_monster(dungeon_level: int) -> str:
    """Get a random monster appropriate for the dungeon level."""
    level_key = str(min(dungeon_level, 6))
    table = _ENCOUNTER_TABLES.get(level_key, _ENCOUNTER_TABLES["1"])
    return random.choice(table)


def get_monster_hit_dice(monster_type: str) -> float:
    """Get the hit dice count for a single monster of this type."""
    return _MONSTERS.get(monster_type, {}).get("hit_dice", 1.0)


def get_monster_count(monster_type: str) -> int:
    """Roll the number appearing for this monster type."""
    expr = _MONSTERS.get(monster_type, {}).get("number_appearing", "1")
    return _roll_dice(expr)


def get_monster_treasure_modifier(monster_type: str) -> float:
    """Get treasure modifier for a monster type."""
    return _MONSTERS.get(monster_type, {}).get("treasure_modifier", 1.0)


def get_monster_ac(monster_type: str) -> int:
    """Get descending AC for a monster type. Default 9 (unarmored)."""
    return _MONSTERS.get(monster_type, {}).get("ac", 9)


def get_monster_morale(monster_type: str) -> int:
    """Get morale rating for a monster type. Default 8."""
    return _MONSTERS.get(monster_type, {}).get("morale", 8)


def is_monster_undead(monster_type: str) -> bool:
    """Return True if this monster type is undead."""
    return _MONSTERS.get(monster_type, {}).get("is_undead", False)


def roll_monster_hd(monster_type: str, count: int) -> int:
    """Roll HD for a group of monsters. Each monster rolls its HD in d8s, summed."""
    hd = get_monster_hit_dice(monster_type)
    total = 0
    for _ in range(count):
        # Roll hd number of d8s per monster (fractional HD = at least 1d8)
        dice_count = max(1, int(hd))
        total += sum(random.randint(1, 8) for _ in range(dice_count))
        # Fractional HD: e.g. 0.5 HD = 1d4 (half a d8)
        fractional = hd - int(hd)
        if fractional > 0:
            half_die = max(1, int(8 * fractional))
            total += random.randint(1, half_die)
    return total

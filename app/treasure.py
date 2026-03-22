"""Treasure generation from JSON config."""

import json
import random
import re
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "treasure.json"

with open(_DATA_PATH) as f:
    TREASURE_CONFIG = json.load(f)


def _roll_dice(expr: str) -> int:
    """Roll dice from an expression like '2d6', '1d10-1', '3d8+2'."""
    if not expr:
        return 0
    match = re.match(r'(\d+)d(\d+)([+-]\d+)?', expr.strip())
    if not match:
        return int(expr)
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    total = sum(random.randint(1, sides) for _ in range(count)) + modifier
    return max(0, total)


def generate_treasure(dungeon_level: int) -> dict:
    """Generate treasure for a given dungeon level using the JSON config.

    Returns {"gold": int, "silver": int, "copper": int, "xp_value": int, "special_item": None, "name": str}
    """
    level_key = str(min(dungeon_level, 6))
    config = TREASURE_CONFIG.get("levels", {}).get(level_key)
    if not config:
        config = TREASURE_CONFIG["levels"]["1"]

    # Roll gold: dice * multiplier + bonus
    gold_roll = _roll_dice(config.get("gold_dice", "2d6"))
    multiplier = config.get("gold_multiplier", dungeon_level * 10)
    bonus = _roll_dice(config.get("gold_bonus_dice", "")) if config.get("gold_bonus_dice") else 0
    gold = gold_roll * multiplier + bonus

    # Optional silver and copper
    silver = _roll_dice(config["silver_dice"]) if config.get("silver_dice") else 0
    copper = _roll_dice(config["copper_dice"]) if config.get("copper_dice") else 0

    name = config.get("name", "Treasure")

    # XP = total value in copper / 100 (i.e. 1 XP per GP equivalent)
    total_copper = gold * 100 + silver * 10 + copper
    xp_value = total_copper // 100

    return {
        "gold": gold,
        "silver": silver,
        "copper": copper,
        "xp_value": xp_value,
        "special_item": None,
        "name": name,
    }

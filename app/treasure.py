"""Treasure generation from OSE dungeon level tables."""

import json
import random
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "treasure.json"

with open(_DATA_PATH) as f:
    TREASURE_CONFIG = json.load(f)


def _get_tier(dungeon_level: int) -> dict:
    for tier in TREASURE_CONFIG["tiers"]:
        if dungeon_level <= tier["max_level"]:
            return tier
    return TREASURE_CONFIG["tiers"][-1]


def generate_treasure(dungeon_level: int) -> dict:
    """Generate treasure for a given dungeon level using OSE tables.

    Silver is always present. Gold appears 50% of the time.
    Gems and jewelry each appear at the tier's listed percentage.
    Magic items appear at the tier's listed percentage.
    Gem/jewelry values are folded into the gold total.
    """
    tier = _get_tier(dungeon_level)

    # Silver: always present, base × 1d(die)
    silver = tier["silver_base"] * random.randint(1, tier["silver_die"])

    # Gold: 50% chance, base × 1d6
    gold = 0
    if random.random() < 0.5:
        gold = tier["gold_base"] * random.randint(1, tier["gold_die"])

    # Gems: percent chance → value in gp folded into gold
    if random.random() < tier["gems_chance"]:
        gold += tier["gems_value"]

    # Jewelry: percent chance → value in gp folded into gold
    if random.random() < tier["jewelry_chance"]:
        gold += tier["jewelry_value"]

    # Magic item: percent chance
    special_item = "Magic Item" if random.random() < tier["magic_chance"] else None

    total_copper = gold * 100 + silver * 10
    xp_value = total_copper // 100  # 1 XP per GP equivalent

    return {
        "gold": gold,
        "silver": silver,
        "copper": 0,
        "xp_value": xp_value,
        "special_item": special_item,
        "name": tier["name"],
    }

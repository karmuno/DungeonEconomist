"""Magic item generation and slot management."""

import json
import random
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "magic_items.json"

with open(_DATA_PATH) as f:
    _ITEM_DATA = json.load(f)


def generate_magic_item(dungeon_level: int = 1) -> dict:
    """Generate a random magic item. Returns {name, item_type, bonus}."""
    item_type = random.choice(["weapon", "armor"])
    prefix = random.choice(_ITEM_DATA["prefixes"])
    base = random.choice(_ITEM_DATA["weapons"] if item_type == "weapon" else _ITEM_DATA["armor"])
    bonus = dungeon_level
    name = f"{prefix} {base} +{bonus}"
    return {"name": name, "item_type": item_type, "bonus": bonus}


def can_equip(adventurer, item_type: str) -> bool:
    """Check if an adventurer has a free slot for this item type.
    Cap: 1 weapon + 1 armor."""
    existing_types = [item.item_type for item in adventurer.magic_items]
    return item_type not in existing_types


def get_weapon_bonus(adventurer) -> int:
    """Total weapon bonus for an adventurer (0 if no weapon)."""
    for item in adventurer.magic_items:
        if item.item_type == "weapon":
            return item.bonus or 0
    return 0


def get_armor_bonus(adventurer) -> int:
    """Total armor bonus for an adventurer (0 if no armor). This is an HP buffer."""
    for item in adventurer.magic_items:
        if item.item_type == "armor":
            return item.bonus or 0
    return 0

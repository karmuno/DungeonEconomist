"""Magic item generation and slot management."""

import json
import random
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "magic_items.json"

with open(_DATA_PATH) as f:
    _ITEM_DATA = json.load(f)


def _weapon_item(dungeon_level: int) -> dict:
    prefix = random.choice(_ITEM_DATA["prefixes"])
    base = random.choice(_ITEM_DATA["weapons"])
    bonus = dungeon_level
    return {"name": f"{prefix} {base} +{bonus}", "item_type": "weapon", "bonus": bonus}


def _armor_item(dungeon_level: int) -> dict:
    prefix = random.choice(_ITEM_DATA["prefixes"])
    base = random.choice(_ITEM_DATA["armor"])
    bonus = dungeon_level
    return {"name": f"{prefix} {base} +{bonus}", "item_type": "armor", "bonus": bonus}


def _ring_item(dungeon_level: int) -> dict:
    base = random.choice(_ITEM_DATA["rings"])
    bonus = dungeon_level
    return {"name": f"{base} +{bonus}", "item_type": "ring", "bonus": bonus}


def _scroll_item() -> dict:
    name = random.choice(_ITEM_DATA["scrolls"])
    return {"name": name, "item_type": "scroll", "bonus": 0, "consumable": True}


def _potion_item(healing: bool = False) -> dict:
    if healing:
        return {"name": "Potion of Healing", "item_type": "potion", "bonus": 0, "consumable": True}
    name = random.choice(_ITEM_DATA["potions"])
    return {"name": name, "item_type": "potion", "bonus": 0, "consumable": True}


def generate_magic_item(dungeon_level: int = 1) -> dict:
    """Generate a random magic item appropriate for the dungeon level.

    Distribution: 35% weapon, 30% armor, 20% ring, 10% scroll, 5% potion.
    """
    roll = random.random()
    if roll < 0.35:
        return _weapon_item(dungeon_level)
    elif roll < 0.65:
        return _armor_item(dungeon_level)
    elif roll < 0.85:
        return _ring_item(dungeon_level)
    elif roll < 0.95:
        return _scroll_item()
    else:
        return _potion_item(healing=True)


def generate_class_magic_item(dungeon_level: int, adventurer_class: str) -> dict:
    """Generate a class-appropriate magic item for Library Tier I discovery."""
    if adventurer_class in ("Fighter", "Dwarf", "Halfling"):
        roll = random.random()
        if roll < 0.40:
            return _weapon_item(dungeon_level)
        elif roll < 0.70:
            return _armor_item(dungeon_level)
        else:
            return _ring_item(dungeon_level)
    elif adventurer_class == "Cleric":
        roll = random.random()
        if roll < 0.40:
            return _potion_item(healing=True)
        elif roll < 0.70:
            return _armor_item(dungeon_level)
        else:
            return _ring_item(dungeon_level)
    elif adventurer_class in ("Magic-User", "Elf"):
        roll = random.random()
        if roll < 0.60:
            return _scroll_item()
        elif roll < 0.80:
            return _weapon_item(dungeon_level)
        else:
            return _ring_item(dungeon_level)
    else:
        return generate_magic_item(dungeon_level)


def can_equip(adventurer, item_type: str) -> bool:
    """Check if an adventurer has a free slot for this item type.

    Slots: 1 weapon, 1 armor, 1 ring. Potions: 1 max. Scrolls/artifacts: unlimited.
    """
    if item_type in ("scroll", "artifact"):
        return True
    existing_types = [item.item_type for item in adventurer.magic_items]
    if item_type == "potion":
        return "potion" not in existing_types
    return item_type not in existing_types


def get_weapon_bonus(adventurer) -> int:
    """Total weapon bonus for an adventurer (0 if no weapon)."""
    for item in adventurer.magic_items:
        if item.item_type == "weapon":
            return item.bonus or 0
    return 0


def get_armor_bonus(adventurer) -> int:
    """Total defensive bonus for an adventurer: armor + ring (both act as HP buffer)."""
    total = 0
    for item in adventurer.magic_items:
        if item.item_type in ("armor", "ring"):
            total += item.bonus or 0
    return total


def has_potion(adventurer) -> bool:
    """Check if adventurer carries a healing potion."""
    return any(item.item_type == "potion" for item in adventurer.magic_items)


def get_scroll_count(adventurer) -> int:
    """Count scrolls carried by an adventurer."""
    return sum(1 for item in adventurer.magic_items if item.item_type == "scroll")


def get_spell_multiplier(adventurer) -> int:
    """Get the total spell multiplier from artifacts (2^N, minimum 1)."""
    artifact_count = sum(1 for item in adventurer.magic_items if item.item_type == "artifact")
    return 2 ** artifact_count if artifact_count > 0 else 1

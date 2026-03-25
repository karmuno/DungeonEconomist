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


def generate_class_magic_item(dungeon_level: int, adventurer_class: str) -> dict:
    """Generate a class-appropriate magic item for Library Tier I discovery.

    Fighters -> weapons & armor, Clerics -> armor & potions,
    M-Us -> scrolls, Elves -> weapons or scrolls, Dwarves -> weapons & armor,
    Halflings -> weapons & armor.
    """
    prefix = random.choice(_ITEM_DATA["prefixes"])
    bonus = dungeon_level

    if adventurer_class in ("Fighter", "Dwarf", "Halfling"):
        item_type = random.choice(["weapon", "armor"])
        base = random.choice(_ITEM_DATA["weapons"] if item_type == "weapon" else _ITEM_DATA["armor"])
        name = f"{prefix} {base} +{bonus}"
        return {"name": name, "item_type": item_type, "bonus": bonus}
    elif adventurer_class == "Cleric":
        roll = random.choice(["armor", "potion"])
        if roll == "potion":
            return {"name": "Healing Potion", "item_type": "potion", "bonus": 0, "consumable": True}
        base = random.choice(_ITEM_DATA["armor"])
        name = f"{prefix} {base} +{bonus}"
        return {"name": name, "item_type": "armor", "bonus": bonus}
    elif adventurer_class in ("Magic-User", "Elf"):
        return {"name": "Arcane Scroll", "item_type": "scroll", "bonus": 0, "consumable": True}
    else:
        item_type = random.choice(["weapon", "armor"])
        base = random.choice(_ITEM_DATA["weapons"] if item_type == "weapon" else _ITEM_DATA["armor"])
        name = f"{prefix} {base} +{bonus}"
        return {"name": name, "item_type": item_type, "bonus": bonus}


def can_equip(adventurer, item_type: str) -> bool:
    """Check if an adventurer has a free slot for this item type.
    Cap: 1 weapon + 1 armor. Potions: 1 max. Scrolls/artifacts: unlimited."""
    if item_type in ("scroll", "artifact"):
        return True  # no limit
    existing_types = [item.item_type for item in adventurer.magic_items]
    if item_type == "potion":
        return "potion" not in existing_types  # max 1 potion
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


def has_potion(adventurer) -> bool:
    """Check if adventurer carries a healing potion."""
    return any(item.item_type == "potion" for item in adventurer.magic_items)


def get_scroll_count(adventurer) -> int:
    """Count scrolls carried by an adventurer."""
    return sum(1 for item in adventurer.magic_items if item.item_type == "scroll")


def get_spell_multiplier(adventurer) -> int:
    """Get the total spell multiplier from artifacts. Stacks multiplicatively.

    Each artifact doubles spell uses; multiple artifacts: 2^N.
    Returns the multiplier (1 if no artifacts).
    """
    artifact_count = sum(1 for item in adventurer.magic_items if item.item_type == "artifact")
    return 2 ** artifact_count if artifact_count > 0 else 1

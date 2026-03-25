"""Character progression and level-up system for Venturekeep.

Class-specific HP and XP values are driven by app/data/classes.json
via the class_config module. XP thresholds are per-class per OSE tables.
"""

from app.class_config import get_hp_config
from app.models import AdventurerClass

# OSE XP tables per class. Index = level (1-based); table[level] = XP required.
# Levels beyond the class max return None from calculate_xp_for_next_level.
_XP_TABLES: dict[str, list[int]] = {
    "Fighter":    [0, 0, 2000,  4000,  8000,  16000,  32000,  64000, 120000, 240000, 360000],
    "Cleric":     [0, 0, 1500,  3000,  6000,  12000,  25000,  50000, 100000, 200000, 300000],
    "Magic-User": [0, 0, 2500,  5000, 10000,  20000,  40000,  80000, 150000, 300000, 450000],
    "Elf":        [0, 0, 4000,  8000, 16000,  32000,  64000, 120000, 250000, 400000, 600000],
    "Dwarf":      [0, 0, 2200,  4400,  8800,  17000,  35000,  70000, 140000, 270000, 400000],
    "Halfling":   [0, 0, 2000,  4000,  8000,  16000,  32000,  64000, 120000],  # OSE max level 8
}

# Per-class level caps (OSE maximums, capped at game max of 10)
_MAX_CLASS_LEVEL: dict[str, int] = {
    "Fighter":    10,
    "Cleric":     10,
    "Magic-User": 10,
    "Elf":        10,
    "Dwarf":      10,
    "Halfling":   8,
}

MAX_LEVEL = 10


def _class_name(adventurer_class: AdventurerClass | str) -> str:
    """Normalize an AdventurerClass enum or string to a class name string."""
    if isinstance(adventurer_class, AdventurerClass):
        return adventurer_class.value
    return adventurer_class


def _get_xp_table(adventurer_class: AdventurerClass | str | None) -> list[int]:
    """Return the XP table for the given class, defaulting to Fighter."""
    if adventurer_class is None:
        return _XP_TABLES["Fighter"]
    return _XP_TABLES.get(_class_name(adventurer_class), _XP_TABLES["Fighter"])


def _get_max_level(adventurer_class: AdventurerClass | str | None) -> int:
    """Return the level cap for the given class."""
    if adventurer_class is None:
        return MAX_LEVEL
    return _MAX_CLASS_LEVEL.get(_class_name(adventurer_class), MAX_LEVEL)


def calculate_xp_for_next_level(
    current_level: int,
    adventurer_class: AdventurerClass | str | None = None,
) -> int | None:
    """Return the XP threshold for the next level, or None if already at class max."""
    max_level = _get_max_level(adventurer_class)
    if current_level >= max_level:
        return None
    table = _get_xp_table(adventurer_class)
    next_level = current_level + 1
    if next_level >= len(table):
        return None
    return table[next_level]


def check_for_level_up(
    current_level: int,
    current_xp: int,
    adventurer_class: AdventurerClass | str | None = None,
) -> bool:
    """Return True if the adventurer has enough XP to advance to the next level."""
    threshold = calculate_xp_for_next_level(current_level, adventurer_class)
    if threshold is None:
        return False
    return current_xp >= threshold


def calculate_hp_gain(adventurer_class: AdventurerClass | str, current_level: int) -> int:
    """Calculate HP gain for a level up based on class (from classes.json)."""
    name = _class_name(adventurer_class)
    base_hp, class_multiplier = get_hp_config(name)

    # Higher levels gain slightly less HP
    level_factor = max(0.8, 1.0 - (current_level * 0.02))

    hp_gain = int(base_hp * class_multiplier * level_factor)
    return max(1, hp_gain)  # Always gain at least 1 HP


def get_class_level_bonuses(adventurer_class: AdventurerClass | str, new_level: int) -> dict:
    """Get cumulative class-specific bonuses for a level.

    Currently returns an empty dict — class bonuses are now handled
    by the combat engine via classes.json. Kept for backward compatibility.
    """
    return {}


def apply_level_ups(adv, keep, events) -> None:
    """Check for and apply level ups to an adventurer, adding events."""
    from app.schemas import GameEvent

    while check_for_level_up(adv.level, adv.xp, adv.adventurer_class):
        old_level = adv.level
        adv.level += 1
        hp_gain = calculate_hp_gain(adv.adventurer_class, old_level)
        adv.hp_max += hp_gain
        adv.hp_current += hp_gain
        events.append(GameEvent(
            type="level_up",
            message=f"{adv.name} leveled up to {adv.level}! (+{hp_gain} HP)",
            first_time=adv.level > (keep.highest_level_achieved or 1),
        ))
        if adv.level > (keep.highest_level_achieved or 1):
            keep.highest_level_achieved = adv.level

"""Character progression and level-up system for Venturekeep.

Class-specific HP and XP values are driven by app/data/classes.json
via the class_config module. XP thresholds are universal (not class-specific).
"""

from app.class_config import get_hp_config, get_xp_multiplier
from app.models import AdventurerClass

# XP thresholds for each level (universal base — multiplied by class XP multiplier)
XP_THRESHOLDS = {
    1: 0,
    2: 2000,
    3: 4000,
    4: 8000,
    5: 16000,
    6: 32000,
    7: 64000,
    8: 120000,
    9: 240000,
    10: 360000,
}

MAX_LEVEL = 10


def _class_name(adventurer_class: AdventurerClass | str) -> str:
    """Normalize an AdventurerClass enum or string to a class name string."""
    if isinstance(adventurer_class, AdventurerClass):
        return adventurer_class.value
    return adventurer_class


def calculate_xp_for_next_level(
    current_level: int,
    adventurer_class: AdventurerClass | str | None = None,
) -> int | None:
    """Calculate the XP needed for the next level, accounting for class XP multiplier."""
    if current_level >= MAX_LEVEL:
        return None
    base = XP_THRESHOLDS[current_level + 1]
    if adventurer_class is not None:
        multiplier = get_xp_multiplier(_class_name(adventurer_class))
        return int(base * multiplier)
    return base


def check_for_level_up(
    current_level: int,
    current_xp: int,
    adventurer_class: AdventurerClass | str | None = None,
) -> bool:
    """Check if an adventurer has enough XP to level up."""
    next_level = current_level + 1
    if next_level > MAX_LEVEL:
        return False
    threshold = XP_THRESHOLDS[next_level]
    if adventurer_class is not None:
        multiplier = get_xp_multiplier(_class_name(adventurer_class))
        threshold = int(threshold * multiplier)
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

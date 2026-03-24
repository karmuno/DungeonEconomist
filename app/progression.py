"""
Character progression and level-up system for Venturekeep
"""
from app.models import AdventurerClass

# XP thresholds for each level (standard progression)
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

# Elves require 2× XP per level
ELF_XP_THRESHOLDS = {level: xp * 2 for level, xp in XP_THRESHOLDS.items()}

# HP gain per level-up. All HD are d6 (spec); values represent average d6 roll
# with small class distinction preserved via +1/+0 rounding.
HP_GAIN_BY_CLASS = {
    AdventurerClass.FIGHTER:    4,  # 1 HD/level × d6
    AdventurerClass.DWARF:      4,  # same as Fighter
    AdventurerClass.HALFLING:   4,  # same as Fighter
    AdventurerClass.ELF:        4,  # Fighter HD (dual class)
    AdventurerClass.CLERIC:     3,  # 1 HD/2 levels × d6
    AdventurerClass.MAGIC_USER: 2,  # 1 HD/3 levels × d6
}

# Class-specific level-up bonuses (hp_multiplier used only in calculate_hp_gain)
CLASS_BONUSES = {
    AdventurerClass.FIGHTER:    {"hp_multiplier": 1.0},
    AdventurerClass.DWARF:      {"hp_multiplier": 1.0},
    AdventurerClass.HALFLING:   {"hp_multiplier": 1.0},
    AdventurerClass.ELF:        {"hp_multiplier": 1.0},
    AdventurerClass.CLERIC:     {"hp_multiplier": 1.0},
    AdventurerClass.MAGIC_USER: {"hp_multiplier": 1.0},
}


def calculate_xp_for_next_level(current_level: int, adventurer_class: AdventurerClass = None) -> int | None:
    """XP needed for the next level. Returns None at max level."""
    if current_level >= 10:
        return None
    table = ELF_XP_THRESHOLDS if adventurer_class == AdventurerClass.ELF else XP_THRESHOLDS
    return table[current_level + 1]


def check_for_level_up(current_level: int, current_xp: int,
                        adventurer_class: AdventurerClass = None) -> bool:
    """True if the adventurer has enough XP to level up."""
    if current_level >= 10:
        return False
    table = ELF_XP_THRESHOLDS if adventurer_class == AdventurerClass.ELF else XP_THRESHOLDS
    return current_xp >= table[current_level + 1]


def calculate_hp_gain(adventurer_class: AdventurerClass, current_level: int) -> int:
    """HP gain on level-up. Slight reduction at higher levels."""
    base_hp = HP_GAIN_BY_CLASS[adventurer_class]
    level_factor = max(0.8, 1.0 - (current_level * 0.02))
    return max(1, int(base_hp * level_factor))


def get_class_level_bonuses(adventurer_class: AdventurerClass, new_level: int) -> dict:
    """Cumulative class-specific bonuses for a level (currently empty for all classes)."""
    base = CLASS_BONUSES[adventurer_class].copy()
    base.pop("hp_multiplier", None)
    return {k: v * (new_level - 1) for k, v in base.items() if isinstance(v, (int, float))}


def apply_level_ups(adv, keep, events) -> None:
    """Check for and apply level-ups to an adventurer, appending GameEvent entries."""
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

"""
Character progression and level-up system for Venturekeep
"""
from app.models import AdventurerClass

# XP thresholds for each level
# Classic progressive scale
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

# Base HP gain per level by class
HP_GAIN_BY_CLASS = {
    AdventurerClass.FIGHTER: 8,  # d8 average = 4.5, + 3 CON
    AdventurerClass.CLERIC: 6,   # d6 average = 3.5, + 2 CON
    AdventurerClass.MAGIC_USER: 4,  # d4 average = 2.5, + 1 CON
    AdventurerClass.ELF: 6,     # d6 average = 3.5, + 2 CON
    AdventurerClass.DWARF: 8,   # d8 average = 4.5, + 3 CON
    AdventurerClass.HOBBIT: 6,  # d6 average = 3.5, + 2 CON
}

# Class-specific bonuses on level up
CLASS_BONUSES = {
    AdventurerClass.FIGHTER: {
        "hp_multiplier": 1.1,
    },
    AdventurerClass.CLERIC: {
        "hp_multiplier": 1.0,
    },
    AdventurerClass.MAGIC_USER: {
        "hp_multiplier": 0.9,
    },
    AdventurerClass.ELF: {
        "hp_multiplier": 1.0,
    },
    AdventurerClass.DWARF: {
        "hp_multiplier": 1.05,
    },
    AdventurerClass.HOBBIT: {
        "hp_multiplier": 0.95,
    }
}

def calculate_xp_for_next_level(current_level: int) -> int:
    """Calculate the XP needed for the next level"""
    if current_level >= 10:  # Max level for MVP
        return None

    return XP_THRESHOLDS[current_level + 1]

def check_for_level_up(current_level: int, current_xp: int) -> bool:
    """Check if an adventurer has enough XP to level up"""
    next_level = current_level + 1
    if next_level > 10:  # Max level for MVP
        return False

    return current_xp >= XP_THRESHOLDS[next_level]

def calculate_hp_gain(adventurer_class: AdventurerClass, current_level: int) -> int:
    """Calculate HP gain for a level up based on class"""
    base_hp = HP_GAIN_BY_CLASS[adventurer_class]
    class_multiplier = CLASS_BONUSES[adventurer_class].get("hp_multiplier", 1.0)

    # Higher levels gain slightly less HP
    level_factor = max(0.8, 1.0 - (current_level * 0.02))

    hp_gain = int(base_hp * class_multiplier * level_factor)
    return max(1, hp_gain)  # Always gain at least 1 HP

def get_class_level_bonuses(adventurer_class: AdventurerClass, new_level: int):
    """Get the cumulative class-specific bonuses for a level"""
    base_bonuses = CLASS_BONUSES[adventurer_class].copy()

    # Remove hp_multiplier as it's only used for HP calculation
    if "hp_multiplier" in base_bonuses:
        del base_bonuses["hp_multiplier"]

    # Calculate cumulative bonuses
    cumulative_bonuses = {}
    for bonus_type, bonus_value in base_bonuses.items():
        # Some bonuses are per-level, others are fixed
        if isinstance(bonus_value, (int, float)):
            if bonus_type.endswith('_bonus'):
                # Fixed bonus per level (like carry capacity)
                cumulative_bonuses[bonus_type] = bonus_value * (new_level - 1)
            else:
                # Percentage bonuses (effectiveness, resistance, etc)
                cumulative_bonuses[bonus_type] = bonus_value * (new_level - 1)

    return cumulative_bonuses


def apply_level_ups(adv, keep, events):
    """Check for and apply level ups to an adventurer, adding events."""
    from app.schemas import GameEvent

    while check_for_level_up(adv.level, adv.xp):
        old_level = adv.level
        adv.level += 1
        hp_gain = calculate_hp_gain(adv.adventurer_class, old_level)
        adv.hp_max += hp_gain
        adv.hp_current += hp_gain
        events.append(GameEvent(
            type="level_up",
            message=f"{adv.name} leveled up to {adv.level}! (+{hp_gain} HP)",
            first_time=adv.level > (keep.highest_level_achieved or 1)
        ))
        # Update highest_level_achieved if this adventurer surpassed it
        if adv.level > (keep.highest_level_achieved or 1):
            keep.highest_level_achieved = adv.level

"""Class configuration loader.

Reads app/data/classes.json and exposes typed accessors for combat,
progression, and ability data. All class-specific numbers live in the
JSON file so they can be tuned without touching code.
"""

import json
import math
import random
import re
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "classes.json"

with open(_DATA_PATH) as f:
    _CONFIG = json.load(f)

_CLASSES: dict = _CONFIG["classes"]
COMBAT_DEFAULTS: dict = _CONFIG["combat_defaults"]


def get_class_config(class_name: str) -> dict:
    """Return the full config dict for a class."""
    if class_name not in _CLASSES:
        raise ValueError(f"Unknown class: {class_name}")
    return _CLASSES[class_name]


def get_combat_hd(class_name: str, level: int) -> int:
    """Return the number of Hit Dice a character has for combat.

    Uses the hd_per_level ratio: ceil(level * num / den).
    A level 1 character always has at least 1 HD.
    """
    cfg = get_class_config(class_name)
    num = cfg["hd_per_level_num"]
    den = cfg["hd_per_level_den"]
    return max(1, math.ceil(level * num / den))


def get_thac0(class_name: str, level: int) -> int:
    """Return THAC0 for a class at a given level."""
    cfg = get_class_config(class_name)
    for entry in cfg["thac0"]:
        if entry["min_level"] <= level <= entry["max_level"]:
            return entry["thac0"]
    # Fallback: use the last entry for levels beyond max
    return cfg["thac0"][-1]["thac0"]


def get_to_hit_bonus(class_name: str) -> int:
    """Return the fixed to-hit bonus for a class (e.g. +1 for Fighters)."""
    return get_class_config(class_name).get("to_hit_bonus", 0)


def get_ability(class_name: str, ability_name: str) -> dict | None:
    """Return the config dict for a specific class ability, or None."""
    cfg = get_class_config(class_name)
    return cfg.get("abilities", {}).get(ability_name)


def get_ability_uses(class_name: str, ability_name: str, level: int) -> int:
    """Evaluate the uses_per_expedition formula for an ability.

    Supported formulas: "level", "level - 1", etc.
    Returns 0 if the ability doesn't exist or has no uses formula.
    """
    ability = get_ability(class_name, ability_name)
    if not ability:
        return 0

    # Check min_level requirement
    min_level = ability.get("min_level", 1)
    if level < min_level:
        return 0

    formula = ability.get("uses_per_expedition", "0")
    return _eval_formula(formula, level)


def get_xp_multiplier(class_name: str) -> float:
    """Return the XP multiplier for a class (e.g. 2.0 for Elf)."""
    return get_class_config(class_name).get("xp_multiplier", 1.0)


def get_hp_config(class_name: str) -> tuple[int, float]:
    """Return (hp_gain_base, hp_multiplier) for level-up calculations."""
    cfg = get_class_config(class_name)
    return cfg["hp_gain_base"], cfg["hp_multiplier"]


def get_hit_die(class_name: str) -> int:
    """Return the hit die size for a class (used for HP rolls on level up)."""
    return get_class_config(class_name)["hit_die"]


def get_spell_name(class_name: str, level: int) -> str:
    """Return the flavor spell name for a caster at the given level.

    Returns the highest-unlocked spell name (e.g. level 5 M-U -> "Fireball").
    """
    ability = get_ability(class_name, "sleep_spell")
    if not ability:
        return "Spell"
    variants = ability.get("flavor_by_level", {})
    # Find the highest level key <= character level
    best_name = "Spell"
    for lvl_key, name in sorted(variants.items(), key=lambda x: int(x[0])):
        if int(lvl_key) <= level:
            best_name = name
    return best_name


def get_turn_undead_target(cleric_level: int, undead_hd: int) -> str | int | None:
    """Look up the turn undead table.

    Returns:
        int: target number to roll on 2d6 (success if roll >= target)
        "T": automatic turn (undead flee)
        "D": automatic destroy
        None: impossible (cleric too low level for this undead HD)
    """
    ability = get_ability("Cleric", "turn_undead")
    if not ability:
        return None
    table = ability.get("table", {})
    level_row = table.get(str(cleric_level))
    if not level_row:
        return None
    result = level_row.get(str(undead_hd))
    if result is None:
        return None
    return result


def get_heal_amount() -> int:
    """Roll the cleric prevent-death heal amount (1d6+2)."""
    ability = get_ability("Cleric", "prevent_death")
    if not ability:
        return 4  # fallback
    dice_expr = ability.get("heal_dice", "1d6+2")
    return _roll_dice(dice_expr)


def has_ability(class_name: str, ability_name: str) -> bool:
    """Check if a class has a given ability."""
    return get_ability(class_name, ability_name) is not None


def list_classes() -> list[str]:
    """Return all configured class names."""
    return list(_CLASSES.keys())


# ---- Internal helpers ----

def _eval_formula(formula: str, level: int) -> int:
    """Safely evaluate a simple level-based formula.

    Supports: "level", "level - 1", "level + 2", "level * 2", plain ints.
    """
    formula = formula.strip()
    if formula.isdigit():
        return int(formula)
    if formula == "level":
        return level
    # Match "level [+-*/] N"
    match = re.match(r"level\s*([+\-*/])\s*(\d+)", formula)
    if match:
        op, n = match.group(1), int(match.group(2))
        if op == "+":
            return level + n
        if op == "-":
            return max(0, level - n)
        if op == "*":
            return level * n
        if op == "/":
            return max(1, level // n)
    return 0


def _roll_dice(expr: str) -> int:
    """Roll a dice expression like '1d6+2'."""
    match = re.match(r"(\d+)d(\d+)([+-]\d+)?", expr)
    if not match:
        return int(expr) if expr.isdigit() else 0
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    return sum(random.randint(1, sides) for _ in range(count)) + modifier

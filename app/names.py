"""Adventurer name generation. Single source of truth for all name creation."""

import json
import random
from pathlib import Path

from app.models import AdventurerClass

_DATA_PATH = Path(__file__).parent / "data" / "names.json"

with open(_DATA_PATH) as f:
    _NAMES = json.load(f)

_FIRST_NAMES = {
    AdventurerClass.FIGHTER: _NAMES["fighter"],
    AdventurerClass.MAGIC_USER: _NAMES["magic_user"],
    AdventurerClass.ELF: _NAMES["elf"],
    AdventurerClass.DWARF: _NAMES["dwarf"],
    AdventurerClass.HALFLING: _NAMES["hobbit"],
}
_SURNAMES = _NAMES["surnames"]
_HALFLING_SURNAMES = _NAMES["hobbit_surnames"]
_CLERIC_TITLES = _NAMES["cleric_titles"]
_CLERIC_GIVEN = _NAMES["cleric_given"]


def generate_adventurer_name(adventurer_class: AdventurerClass) -> str:
    """Generate a random name for a new adventurer."""
    if adventurer_class == AdventurerClass.CLERIC:
        title = random.choice(_CLERIC_TITLES)
        given = random.choice(_CLERIC_GIVEN)
        surname = random.choice(_SURNAMES)
        return f"{title} {given} {surname}"

    first = random.choice(_FIRST_NAMES.get(adventurer_class, _FIRST_NAMES[AdventurerClass.FIGHTER]))

    if adventurer_class == AdventurerClass.HALFLING:
        surname = random.choice(_SURNAMES + _HALFLING_SURNAMES)
    else:
        surname = random.choice(_SURNAMES)

    return f"{first} {surname}"

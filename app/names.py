"""Adventurer name generation. Single source of truth for all name creation."""

import random
from app.models import AdventurerClass
from app.data.names import (
    FIGHTER_NAMES, CLERIC_TITLES, CLERIC_GIVEN_NAMES, MAGIC_USER_NAMES,
    ELF_NAMES, DWARF_NAMES, HOBBIT_NAMES, SURNAMES, HOBBIT_SURNAMES,
)

_FIRST_NAMES = {
    AdventurerClass.FIGHTER: FIGHTER_NAMES,
    AdventurerClass.MAGIC_USER: MAGIC_USER_NAMES,
    AdventurerClass.ELF: ELF_NAMES,
    AdventurerClass.DWARF: DWARF_NAMES,
    AdventurerClass.HOBBIT: HOBBIT_NAMES,
}


def generate_adventurer_name(adventurer_class: AdventurerClass) -> str:
    """Generate a random name for a new adventurer."""
    if adventurer_class == AdventurerClass.CLERIC:
        title = random.choice(CLERIC_TITLES)
        given = random.choice(CLERIC_GIVEN_NAMES)
        surname = random.choice(SURNAMES)
        return f"{title} {given} {surname}"

    first = random.choice(_FIRST_NAMES.get(adventurer_class, FIGHTER_NAMES))

    if adventurer_class == AdventurerClass.HOBBIT:
        surname = random.choice(SURNAMES + HOBBIT_SURNAMES)
    else:
        surname = random.choice(SURNAMES)

    return f"{first} {surname}"

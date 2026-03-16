"""Magic item generation."""

import json
import random
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "magic_items.json"

with open(_DATA_PATH) as f:
    _ITEM_DATA = json.load(f)


def generate_magic_item() -> dict:
    """Generate a random magic item. Returns {name, item_type}."""
    item_type = random.choice(["weapon", "armor"])
    prefix = random.choice(_ITEM_DATA["prefixes"])
    base = random.choice(_ITEM_DATA["weapons"] if item_type == "weapon" else _ITEM_DATA["armor"])
    suffix = random.choice(_ITEM_DATA["suffixes"])
    name = f"{prefix} {base} {suffix}"
    return {"name": name, "item_type": item_type}

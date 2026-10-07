"""Offline lethality sweep: how many adventurers a fresh level-1 party of six loses to a
monster at a given number appearing, measured by running the real combat resolver.

    python scripts/number_appearing_sweep.py
    python scripts/number_appearing_sweep.py --trials 1000 --monster Wolf --dice 2d6 1d6 1d4

Every fight starts from full HP with no potions, no buildings and no magic items, so the
numbers here run *lower* than a mid-delve fight with a wounded party. Read them against the
calibration rows (Goblin, Orc, Skeleton at their current dice), whose in-game rates from
the balance keeps are about 0.5 deaths per fight.
"""

import argparse
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import app.monsters as monsters_module  # noqa: E402
from app.expedition import Expedition  # noqa: E402
from app.models import AdventurerClass  # noqa: E402
from app.routes.keeps import roll_hp  # noqa: E402

# Current dice first, then the candidates, per monster at or above 1.0 deaths per fight
# in the all-time ranking of 2026-09-15. Calibration rows carry only their current dice.
SWEEP: dict[str, list[str]] = {
    "Wolf": ["2d6", "1d6", "1d4", "1d3", "1d2"],
    "Halfling": ["3d6", "2d4", "1d6", "1d4"],
    "Kobold": ["4d4", "2d4", "1d6", "1d4"],
    "Troglodyte": ["1d8", "1d4", "1d3", "1d2"],
    "Sprite": ["3d6", "2d4", "1d6", "1d4"],
    "Giant Gecko": ["1d3", "1d2", "1"],
    "Fire Beetle": ["1d8", "1d4", "1d3"],
    "Killer Bee": ["1d10", "1d6", "1d4"],
    "Rock Baboon": ["2d6", "1d6", "1d4"],
    "Goblin": ["2d4"],
    "Orc": ["2d4"],
    "Skeleton": ["3d4"],
}


def fresh_party() -> list[dict]:
    """One of each class at level 1, rolled like a recruit, geared like a day-one keep."""
    party = []
    for cls in AdventurerClass:
        hp = roll_hp(cls)
        party.append({
            "id": len(party) + 1,
            "name": cls.value,
            "character_class": cls.value,
            "level": 1,
            "base_level": 1,
            "hit_points": hp,
            "current_hp": hp,
            "weapon_bonus": 0,
            "armor_reduction": 0,
            "building_to_hit_bonus": 0,
            "building_damage_bonus": 0,
            "morale_penalty": 0,
            "has_potion": False,
            "scroll_count": 0,
            "spell_multiplier": 1,
        })
    return party


def run(monster: str, dice: str, trials: int) -> tuple[float, float, float]:
    """(deaths per fight, party-fled share, average number appearing) over `trials` fights."""
    original = monsters_module._MONSTERS[monster]["number_appearing"]
    monsters_module._MONSTERS[monster]["number_appearing"] = dice
    deaths = fled = appearing = 0
    try:
        for _ in range(trials):
            exp = Expedition(fresh_party(), dungeon_level=1)
            result = exp.resolve_combat(monster)
            deaths += sum(1 for m in exp.party if m["current_hp"] <= 0)
            fled += 1 if result.get("outcome") == "Party Fled" else 0
            appearing += result.get("monster_count", 0)
    finally:
        monsters_module._MONSTERS[monster]["number_appearing"] = original
    return deaths / trials, fled / trials, appearing / trials


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--trials", type=int, default=400)
    parser.add_argument("--monster", help="sweep one monster only")
    parser.add_argument("--dice", nargs="*", help="candidate dice for --monster (default: the built-in list)")
    parser.add_argument("--seed", type=int, default=20260915)
    args = parser.parse_args()
    random.seed(args.seed)

    sweep = SWEEP
    if args.monster:
        sweep = {args.monster: args.dice or SWEEP.get(args.monster, [monsters_module._MONSTERS[args.monster]["number_appearing"]])}

    print(f"{'monster':<14}{'dice':>6}{'avg#':>7}{'deaths/fight':>14}{'fled':>7}")
    for monster, candidates in sweep.items():
        hd = monsters_module.get_monster_hit_dice(monster)
        for dice in candidates:
            d, f, n = run(monster, dice, args.trials)
            tag = "  (current)" if dice == monsters_module._MONSTERS[monster]["number_appearing"] else ""
            print(f"{monster:<14}{dice:>6}{n:>7.1f}{d:>14.2f}{f * 100:>6.0f}%  HD {hd:g}{tag}")
        print()


if __name__ == "__main__":
    main()

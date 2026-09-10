"""Survivability and progression statistics for a VentureKeep save.

Answers the question the cohort cannot: are adventurers living long enough to become
attached to? Reads whatever database `DATABASE_URL` points at, falling back to the local
SQLite file exactly as the app does.

    python scripts/balance_stats.py

A baseline taken on 2026-09-09, before party morale dropped from 11 to 7, is printed
alongside the current figures so a balance change can be judged rather than guessed at.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402  (importing app also loads .env)
from app.expedition import PARTY_MORALE  # noqa: E402

# Measured 2026-09-09 on Cody's development keep: 969 adventurers, 468 expeditions,
# party morale 11. Kept so a later run shows movement rather than a bare number.
#
# Caveat: this baseline predates the fix for dead adventurers rejoining expeditions, so it
# includes delves staffed partly by ghosts, whose attacks and hit points skewed the odds in
# an unknown direction. Re-baseline once that lands.
BASELINE = {
    "date": "2026-09-09",
    "morale": 11,
    "total": 969,
    "dead_pct": 81.8,
    "deaths_at_level_1_pct": 97.5,
    "reached_level_2_pct": 3.9,
}


def q(session, sql: str) -> list[tuple]:
    """Run a read-only query and return its rows."""
    return list(session.execute(text(sql)).fetchall())


def scalar(session, sql: str) -> int:
    """Run a query returning a single count."""
    rows = q(session, sql)
    return int(rows[0][0]) if rows else 0


def pct(n: int, d: int) -> float:
    """Percentage, treating a zero denominator as zero."""
    return (n / d * 100) if d else 0.0


def delta(current: float, baseline: float) -> str:
    """Signed movement against the baseline, for printing."""
    diff = current - baseline
    arrow = "+" if diff >= 0 else ""
    return f"({arrow}{diff:.1f} vs {baseline:.1f} on {BASELINE['date']})"


def survival(session) -> None:
    """The headline: how many die, at what level, and how many ever advance."""
    total = scalar(session, "SELECT COUNT(*) FROM adventurers")
    dead = scalar(session, "SELECT COUNT(*) FROM adventurers WHERE is_dead = true")
    living = scalar(session, "SELECT COUNT(*) FROM adventurers WHERE is_dead = false AND is_bankrupt = false")
    reached2 = scalar(session, "SELECT COUNT(*) FROM adventurers WHERE level >= 2")

    print("== Survival ==")
    print(f"  {total} adventurers | {dead} dead | {living} living")
    print(f"  dead:            {pct(dead, total):5.1f}%  {delta(pct(dead, total), BASELINE['dead_pct'])}")
    print(f"  reached level 2: {pct(reached2, total):5.1f}%  "
          f"{delta(pct(reached2, total), BASELINE['reached_level_2_pct'])}")

    deaths = q(session, "SELECT level, COUNT(*) FROM adventurers WHERE is_dead = true GROUP BY level ORDER BY level")
    at_one = next((int(n) for lvl, n in deaths if lvl == 1), 0)
    print(f"  deaths at Lv1:   {pct(at_one, dead):5.1f}%  {delta(pct(at_one, dead), BASELINE['deaths_at_level_1_pct'])}")
    print("\n  deaths by level:")
    for lvl, n in deaths:
        print(f"    Lv{str(lvl):<3} {int(n):5d}  {'#' * min(int(n) // 8, 50)}")

    print("\n  living by level:")
    rows = q(session, "SELECT level, COUNT(*) FROM adventurers "
                      "WHERE is_dead = false AND is_bankrupt = false GROUP BY level ORDER BY level")
    for lvl, n in rows:
        print(f"    Lv{str(lvl):<3} {int(n):5d}")


def progression(session) -> None:
    """How close the dead got to advancing, which sizes the XP gap."""
    rows = q(session, "SELECT xp FROM adventurers WHERE is_dead = true AND level = 1")
    xps = sorted(int(r[0]) for r in rows if r[0] is not None)
    if not xps:
        return
    n = len(xps)
    print("\n== Progression ==")
    print(f"  XP of dead level-1s (n={n}): median {xps[n // 2]} | "
          f"75th {xps[int(n * 0.75)]} | 90th {xps[int(n * 0.9)]} | max {xps[-1]}")
    print("  Level 2 needs roughly 2000-2500 depending on class.")


def delving(session) -> None:
    """Where delves happen and how they end."""
    print("\n== Delving ==")
    print("  expeditions by depth:")
    for depth, n in q(session, "SELECT dungeon_level, COUNT(*) FROM expeditions "
                               "GROUP BY dungeon_level ORDER BY dungeon_level"):
        print(f"    depth {str(depth):<5} {int(n)}")
    print("  results:")
    for result, n in q(session, "SELECT result, COUNT(*) FROM expeditions GROUP BY result ORDER BY COUNT(*) DESC"):
        print(f"    {str(result):<16} {int(n)}")


def gear(session) -> None:
    """Whether the dying carry anything, which decides if item changes can help them."""
    print("\n== Gear ==")
    rows = q(session, "SELECT a.level, COUNT(DISTINCT a.id), COUNT(m.id) FROM adventurers a "
                      "LEFT JOIN magic_items m ON m.adventurer_id = a.id "
                      "WHERE a.is_dead = true GROUP BY a.level ORDER BY a.level")
    for lvl, advs, items in rows:
        per = int(items) / max(int(advs), 1)
        print(f"    Lv{str(lvl):<3} {int(advs):5d} dead, {int(items):4d} items held ({per:.2f} each)")
    print("  items in the world:")
    for item_type, n in q(session, "SELECT item_type, COUNT(*) FROM magic_items "
                                   "GROUP BY item_type ORDER BY COUNT(*) DESC"):
        print(f"    {str(item_type):<10} {int(n)}")


def morale() -> None:
    """Retreat likelihood implied by the current PARTY_MORALE constant."""
    outcomes = [a + b for a in range(1, 7) for b in range(1, 7)]

    def fail(m: int) -> float:
        return sum(1 for r in outcomes if r > m) / len(outcomes) * 100

    p = fail(PARTY_MORALE) / 100
    print("\n== Morale ==")
    print(f"  PARTY_MORALE = {PARTY_MORALE} (baseline {BASELINE['morale']})")
    print(f"  one check fails:            {p * 100:5.1f}%")
    print(f"  retreats per lethal combat: {(1 - (1 - p) ** 2) * 100:5.1f}%  (up to two checks)")
    print("  for comparison:")
    for m in (7, 8, 9, 10, 11):
        print(f"    morale {m:2d}: {fail(m):5.1f}% per check")


def main() -> None:
    session = SessionLocal()
    try:
        survival(session)
        progression(session)
        delving(session)
        gear(session)
        morale()
    finally:
        session.close()


if __name__ == "__main__":
    main()

"""Survivability and progression statistics for a VentureKeep save.

Answers the question the cohort cannot: are adventurers living long enough to become
attached to? Reads whatever database `DATABASE_URL` points at, falling back to the local
SQLite file exactly as the app does.

    python scripts/balance_stats.py                # every keep in the database
    python scripts/balance_stats.py --keep 26      # one keep, by id
    python scripts/balance_stats.py --keep "New Balance Test"
    python scripts/balance_stats.py --keep 26 --keep 27   # pooled

The baseline printed beside the current figures is keep "Monster Balance Test" (#30), 420
days, run 2026-09-15 under every current rule: XP pooled for the run's survivors, kills paid
on a flee, number appearing trimmed at the lethal end, magic weapons to-hit and damage only,
party morale 7, all four buildings standing.
Earlier runs, for the record: #28 under per-fight XP shares (125 adventurers, 92.0% dead,
1.6% reached level 2); #26 and #27 pooled under the even split (193 adventurers, 96.9% dead,
0.5% reached level 2); and the 2026-09-09 figures (969 adventurers, 81.8% dead, 3.9%
reached level 2, morale 11), which predate the ghost-adventurer fix.
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402  (importing app also loads .env)
from app.expedition import PARTY_MORALE  # noqa: E402

# Measured 2026-09-15 on keep #30 in Cody's dev database: 65 adventurers, 66 completed
# expeditions over 420 days, all at depth 1, every building standing, every current rule in
# force. Kept so a later run shows movement rather than a bare number.
BASELINE = {
    "date": "2026-09-15",
    "morale": 7,
    "total": 65,
    "dead_pct": 81.5,
    "deaths_at_level_1_pct": 100.0,
    "reached_level_2_pct": 3.1,
}


# Set by main() from --keep; empty means the whole database.
KEEP_IDS: list[int] = []


def where(*conds: str, keep_col: str = "keep_id") -> str:
    """A WHERE clause from the given conditions plus the keep scope, if one is set."""
    parts = [c for c in conds if c]
    if KEEP_IDS:
        parts.append(f"{keep_col} IN ({', '.join(str(k) for k in KEEP_IDS)})")
    return ("WHERE " + " AND ".join(parts)) if parts else ""


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
    total = scalar(session, f"SELECT COUNT(*) FROM adventurers {where()}")
    dead = scalar(session, f"SELECT COUNT(*) FROM adventurers {where('is_dead = true')}")
    living = scalar(session, f"SELECT COUNT(*) FROM adventurers {where('is_dead = false', 'is_bankrupt = false')}")
    reached2 = scalar(session, f"SELECT COUNT(*) FROM adventurers {where('level >= 2')}")

    print("== Survival ==")
    print(f"  {total} adventurers | {dead} dead | {living} living")
    print(f"  dead:            {pct(dead, total):5.1f}%  {delta(pct(dead, total), BASELINE['dead_pct'])}")
    print(f"  reached level 2: {pct(reached2, total):5.1f}%  "
          f"{delta(pct(reached2, total), BASELINE['reached_level_2_pct'])}")

    deaths = q(session, f"SELECT level, COUNT(*) FROM adventurers {where('is_dead = true')} "
                        "GROUP BY level ORDER BY level")
    at_one = next((int(n) for lvl, n in deaths if lvl == 1), 0)
    print(f"  deaths at Lv1:   {pct(at_one, dead):5.1f}%  {delta(pct(at_one, dead), BASELINE['deaths_at_level_1_pct'])}")
    print("\n  deaths by level:")
    for lvl, n in deaths:
        print(f"    Lv{str(lvl):<3} {int(n):5d}  {'#' * min(int(n) // 8, 50)}")

    print("\n  living by level:")
    rows = q(session, f"SELECT level, COUNT(*) FROM adventurers "
                      f"{where('is_dead = false', 'is_bankrupt = false')} GROUP BY level ORDER BY level")
    for lvl, n in rows:
        print(f"    Lv{str(lvl):<3} {int(n):5d}")


def progression(session) -> None:
    """How close the dead got to advancing, which sizes the XP gap."""
    rows = q(session, f"SELECT xp FROM adventurers {where('is_dead = true', 'level = 1')}")
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
    for depth, n in q(session, "SELECT e.dungeon_level, COUNT(*) FROM expeditions e "
                               "JOIN parties p ON p.id = e.party_id "
                               f"{where(keep_col='p.keep_id')} GROUP BY e.dungeon_level ORDER BY e.dungeon_level"):
        print(f"    depth {str(depth):<5} {int(n)}")
    print("  results:")
    for result, n in q(session, "SELECT e.result, COUNT(*) FROM expeditions e JOIN parties p ON p.id = e.party_id "
                                f"{where(keep_col='p.keep_id')} GROUP BY e.result ORDER BY COUNT(*) DESC"):
        print(f"    {str(result):<16} {int(n)}")


def deaths_by_depth(session) -> None:
    """Where deaths actually happen, by dungeon depth rather than character level.

    Also reports the average level of the dead at each depth. A living adventurer's level
    keeps changing after any given delve, so it cannot say what level they were on a past
    expedition; the dead are the only population whose level is frozen at the moment it
    happened, so this is restricted to them rather than quietly averaging in a survivor's
    current (and possibly much later, much higher) level. It answers "how leveled is whoever
    actually dies here", not "how leveled is the party sent to this depth" — the latter would
    need level reconstructed from adventurer_levelled events, not the adventurers table.
    """
    delvers = dict(q(session, "SELECT e.dungeon_level, COUNT(*) FROM expedition_logs l "
                              "JOIN expeditions e ON e.id = l.expedition_id "
                              "JOIN parties p ON p.id = e.party_id "
                              f"{where(keep_col='p.keep_id')} GROUP BY e.dungeon_level"))
    dead_clause = where("l.status = 'dead'", keep_col='p.keep_id')
    deaths = dict(q(session, "SELECT e.dungeon_level, COUNT(*) FROM expedition_logs l "
                             "JOIN expeditions e ON e.id = l.expedition_id "
                             "JOIN parties p ON p.id = e.party_id "
                             f"{dead_clause} GROUP BY e.dungeon_level"))
    avg_death_level = dict(q(session, "SELECT e.dungeon_level, AVG(a.level) FROM expedition_logs l "
                                      "JOIN expeditions e ON e.id = l.expedition_id "
                                      "JOIN parties p ON p.id = e.party_id "
                                      "JOIN adventurers a ON a.id = l.adventurer_id "
                                      f"{dead_clause} GROUP BY e.dungeon_level"))
    print("\n== Deaths by dungeon depth ==")
    print("  depth   delvers   deaths   lethality   avg level of the dead")
    for depth in sorted(delvers):
        n_delvers = int(delvers[depth])
        n_deaths = int(deaths.get(depth, 0))
        level = f"{float(avg_death_level[depth]):.1f}" if depth in avg_death_level else "-"
        print(f"    {str(depth):<5} {n_delvers:7d}   {n_deaths:5d}   {pct(n_deaths, n_delvers):6.1f}%   {level:>12}")


def gear(session) -> None:
    """Whether the dying carry anything, which decides if item changes can help them."""
    print("\n== Gear ==")
    rows = q(session, "SELECT a.level, COUNT(DISTINCT a.id), COUNT(m.id) FROM adventurers a "
                      "LEFT JOIN magic_items m ON m.adventurer_id = a.id "
                      f"{where('a.is_dead = true', keep_col='a.keep_id')} GROUP BY a.level ORDER BY a.level")
    for lvl, advs, items in rows:
        per = int(items) / max(int(advs), 1)
        print(f"    Lv{str(lvl):<3} {int(advs):5d} dead, {int(items):4d} items held ({per:.2f} each)")
    print("  items in the world:")
    for item_type, n in q(session, "SELECT m.item_type, COUNT(*) FROM magic_items m "
                                   "JOIN adventurers a ON a.id = m.adventurer_id "
                                   f"{where(keep_col='a.keep_id')} GROUP BY m.item_type ORDER BY COUNT(*) DESC"):
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


def resolve_keep(session, keep: str) -> tuple[int, str, int]:
    """(id, name, current_day) for a keep given by id or exact name."""
    if keep.isdigit():
        rows = session.execute(text("SELECT id, name, current_day FROM keeps WHERE id = :id"), {"id": int(keep)})
    else:
        rows = session.execute(text("SELECT id, name, current_day FROM keeps WHERE name = :name"), {"name": keep})
    row = rows.fetchone()
    if row is None:
        sys.exit(f"No keep matches {keep!r}")
    return int(row[0]), str(row[1]), int(row[2])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--keep", action="append", default=[],
                        help="scope to a keep, by id or exact name; repeat to pool several (default: every keep)")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        for keep in args.keep:
            keep_id, name, day = resolve_keep(session, keep)
            KEEP_IDS.append(keep_id)
            print(f"keep: {name} (#{keep_id}), day {day}")
        if KEEP_IDS:
            print()
        survival(session)
        progression(session)
        delving(session)
        deaths_by_depth(session)
        gear(session)
        morale()
    finally:
        session.close()


if __name__ == "__main__":
    main()

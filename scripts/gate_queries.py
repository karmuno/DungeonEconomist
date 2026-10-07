"""The v1.0 decision-gate queries: did the cohort ever enter the core loop?

Reads whatever database `DATABASE_URL` points at, falling back to the local SQLite file
exactly as the app does. See buildplans/player-events-spec.md for the event list, payloads
and the four questions this answers. Not an analytics pipeline — one pass over
`player_events`, aggregated in Python so it runs the same way against SQLite or Postgres.

    python scripts/gate_queries.py                  # every account
    python scripts/gate_queries.py --username cody   # one account's full timeline

Per account:
  1. Did they enter the core loop?  first `expedition_started`
  2. Where did they leave?          their last event, whatever it was
  3. Did they return?               count and last time of `return_session`
  4. Death or level-up?             first `adventurer_died` / first `adventurer_levelled`
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.database import SessionLocal  # noqa: E402  (importing app also loads .env)
from app.models import Account, PlayerEvent  # noqa: E402
from app.player_events import EventType  # noqa: E402


def fmt(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "-"


def first_at(events: list[PlayerEvent], event_type: EventType):
    for e in events:
        if e.event_type_id == event_type.value:
            return e.created_at
    return None


def count_of(events: list[PlayerEvent], event_type: EventType) -> int:
    return sum(1 for e in events if e.event_type_id == event_type.value)


def per_player_summary(accounts: list[Account], events_by_user: dict[int, list[PlayerEvent]]) -> None:
    """One row per account: all four gate questions at once."""
    print("== Per-player summary ==")
    rows = []
    for account in accounts:
        events = events_by_user.get(account.id, [])
        rows.append({
            "username": account.username,
            "joined": account.created_at,
            "entered_loop": first_at(events, EventType.EXPEDITION_STARTED),
            "expeditions": count_of(events, EventType.EXPEDITION_COMPLETED),
            "returns": count_of(events, EventType.RETURN_SESSION),
            "first_death": first_at(events, EventType.ADVENTURER_DIED),
            "first_level_up": first_at(events, EventType.ADVENTURER_LEVELLED),
            "wipes": count_of(events, EventType.TPK),
            "last_seen": max((e.created_at for e in events), default=None),
        })
    rows.sort(key=lambda r: r["last_seen"] or r["joined"], reverse=True)

    header = f"  {'username':<20} {'joined':<17} {'entered loop':<17} {'exp':>4} {'ret':>4} " \
             f"{'1st death':<17} {'1st lvl-up':<17} {'wipes':>5} {'last seen':<17}"
    print(header)
    for r in rows:
        print(f"  {r['username']:<20} {fmt(r['joined']):<17} {fmt(r['entered_loop']):<17} "
              f"{r['expeditions']:>4} {r['returns']:>4} {fmt(r['first_death']):<17} "
              f"{fmt(r['first_level_up']):<17} {r['wipes']:>5} {fmt(r['last_seen']):<17}")

    never_entered = [r["username"] for r in rows if r["entered_loop"] is None]
    if never_entered:
        print(f"\n  never entered the core loop: {', '.join(never_entered)}")


def where_did_they_leave(accounts: list[Account], events_by_user: dict[int, list[PlayerEvent]]) -> None:
    """Q2: the last thing each player did before going quiet."""
    print("\n== Where did they leave ==")
    for account in accounts:
        events = events_by_user.get(account.id, [])
        if not events:
            print(f"  {account.username:<20} never did anything past account creation")
            continue
        last = max(events, key=lambda e: e.created_at)
        print(f"  {account.username:<20} {fmt(last.created_at):<17} {last.event_type_id:<28} {last.payload or ''}")


def the_wipes(events_by_user: dict[int, list[PlayerEvent]], accounts_by_id: dict[int, Account]) -> None:
    """Every TPK, in full — the sharpest attachment signal the cohort can produce."""
    print("\n== The wipes, in full ==")
    wipes = [
        (accounts_by_id[uid].username, e)
        for uid, events in events_by_user.items()
        for e in events
        if e.event_type_id == EventType.TPK.value
    ]
    if not wipes:
        print("  none yet")
        return
    wipes.sort(key=lambda pair: pair[1].created_at)
    for username, e in wipes:
        p = e.payload or {}
        print(f"  {fmt(e.created_at):<17} {username:<20} keep #{e.keep_id} "
              f"{p.get('party_name', '?'):<20} depth {p.get('dungeon_level', '?')} "
              f"lost {p.get('adventurers_lost', '?')} avg lvl {p.get('party_avg_level', '?')} "
              f"to {p.get('monster_count', '?')}x {p.get('monster_type', '?')}")


def player_timeline(username: str, accounts_by_username: dict[str, Account],
                     events_by_user: dict[int, list[PlayerEvent]]) -> None:
    """Every event for one player, in order — for reading their whole story once flagged."""
    account = accounts_by_username.get(username)
    if account is None:
        sys.exit(f"No account named {username!r}")
    events = events_by_user.get(account.id, [])
    print(f"== Timeline: {username} (joined {fmt(account.created_at)}) ==")
    if not events:
        print("  no events recorded")
        return
    for e in events:
        print(f"  {fmt(e.created_at):<17} keep #{str(e.keep_id or '-'):<5} {e.event_type_id:<28} {e.payload or ''}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--username", help="print one account's full timeline instead of the summary reports")
    args = parser.parse_args()

    session = SessionLocal()
    try:
        accounts = session.query(Account).order_by(Account.created_at).all()
        accounts_by_username = {a.username: a for a in accounts}
        accounts_by_id = {a.id: a for a in accounts}

        events_by_user: dict[int, list[PlayerEvent]] = {}
        for e in session.query(PlayerEvent).order_by(PlayerEvent.created_at).all():
            events_by_user.setdefault(e.user_id, []).append(e)

        if args.username:
            player_timeline(args.username, accounts_by_username, events_by_user)
            return

        if not accounts:
            print("No accounts yet.")
            return

        per_player_summary(accounts, events_by_user)
        where_did_they_leave(accounts, events_by_user)
        the_wipes(events_by_user, accounts_by_id)
    finally:
        session.close()


if __name__ == "__main__":
    main()

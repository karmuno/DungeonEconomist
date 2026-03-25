# Auto-Delve Bug Report

Audit performed 2026-03-25. All bugs verified by reading `app/routes/game.py` (`_advance_one_day`, `_finalize_expedition`) and `app/expedition.py`.

---

## Bug 1 — `auto_delve_full` permanently blocks relaunch after member death

**File:** `app/routes/game.py`, line ~271 (inside `_advance_one_day`)

**What happens:** `auto_delve_full` requires ALL party members to be at full HP before launching. If any member dies on an expedition, they are removed from the party but surviving members are rarely at full HP. The flag stays `True` indefinitely and the readiness check never passes again.

**Impact:** Auto-delve silently stops working after the first casualty. The player gets no notification and must manually disable the flag.

**Fix needed:** Either clear `auto_delve_full` after a death, or add a fallback that ignores the full-HP requirement once a death has occurred. Also needs a game event ("auto-delve paused: party not at full strength").

---

## Bug 2 — TPK leaves ghost party with stale auto-delve flags

**Files:** `app/routes/game.py` (`_finalize_expedition`, ~line 380), `app/routes/adventurers.py` (auto-delete logic)

**What happens:** When all party members die (TPK), `_finalize_expedition` removes dead members from the party. The auto-delete hook that cleans up the empty party only fires through the adventurer DELETE API endpoint — it does NOT fire from within `_finalize_expedition`. The party record survives with zero members and `auto_delve=True`.

On the next `_advance_one_day`, the auto-delve block checks `not party.on_expedition` (True) and `len(party.members) > 0` (False — 0 members), so no expedition launches. But the flags remain set and no event is emitted. The party is an invisible ghost.

**Impact:** Orphaned party records accumulate. Auto-delve machinery runs its guard clause every day forever, silently. Player may not realise the party is gone.

**Fix needed:** Call the party cleanup logic from `_finalize_expedition` when the last member is removed. Or at minimum emit a "party wiped out" event and disable all auto-delve flags.

---

## Bug 3 — Silent auto-delve failure (no event when readiness not met)

**File:** `app/routes/game.py`, lines ~285–292

**What happens:**
```python
exp_result = _auto_launch_expedition(db, keep, party)
if exp_result:
    events.append(...)
```
There is no `else` branch. If the party is not ready (healing in progress, wrong dungeon level, not enough members, etc.), nothing is logged. The player cannot tell why auto-delve didn't fire.

**Impact:** Auto-delve appears to "just stop working" with no feedback.

**Fix needed:** Add an `else` branch that emits a game event with the reason readiness was not met (e.g., "auto-delve skipped: members below full HP").

---

## Bug 4 — `auto_delve_level` not validated

**File:** `app/routes/game.py` and wherever `auto_delve_level` is set (frontend or route handler)

**What happens:** `auto_delve_level` is an integer that controls the dungeon depth used for auto-launched expeditions. There is no validation that it is ≥ 1. If it is set to 0 or a negative number, the expedition is launched against dungeon level 0 (or invalid), which is either a crash or produces nonsensical combat results.

**Impact:** Potential runtime error or degenerate expedition (0 monsters, 0 XP).

**Fix needed:** Clamp `auto_delve_level` to `max(1, value)` when writing it, or add a validator in the Pydantic schema.

---

## Priority

| # | Bug | Severity |
|---|-----|----------|
| 1 | `auto_delve_full` blocks relaunch after death | High — silently breaks auto-delve for any party that takes casualties |
| 2 | TPK ghost party | Medium — UX confusion, orphaned DB records |
| 3 | Silent failure, no event | Medium — player has no feedback |
| 4 | `auto_delve_level` not validated | Low — only triggered by bad input |

# Player Events — v0.9.1 Spec

**Status: implemented 2026-09-12** (`app/player_events.py`, migration `d5e1f2a3b4c6`, tests in
`tests/test_main_utils.py`). The admin command that runs the gate queries is weekend two.

Scope: see what the first cohort does, so the decision gate can be answered with evidence.
One table (plus a lookup), one helper, insert calls at the right spots. Not an analytics
pipeline. Records from the moment v0.9.1 deploys; the admin query (weekend two) reads it.

The four questions this table must answer, from the roadmap:

1. Did they enter the core loop?
2. Where did they leave?
3. Did they return?
4. Did they reach a death or a level-up?

The queries at the bottom answer them. If a schema change would stop one of them answering,
the change is wrong.

---

## Schema

### `event_types`

Lookup table. Varchar PK so joins read like English. Rows are seeded by the migration that
creates the table; a new type is a new migration with one INSERT, no schema change.

| Column        | Type        | Notes              |
|---------------|-------------|--------------------|
| `id`          | VARCHAR PK  | Slug               |
| `description` | VARCHAR     | Human-readable     |

The Python side mirrors the ids as an `enum.Enum` (`EventType`) in `app/player_events.py`,
per the Python style rules, and the migration seeds the lookup from that enum so the two
cannot drift.

### `player_events`

One row per event. Narrow table with a JSON column for event-specific details.

| Column          | Type                        | Notes                                          |
|-----------------|-----------------------------|-------------------------------------------------|
| `id`            | INT PK                      | Auto-increment                                  |
| `event_type_id` | VARCHAR FK → event_types.id | Indexed                                         |
| `user_id`       | INT FK → accounts.id        | Who. Indexed                                    |
| `keep_id`       | INT FK → keeps.id, nullable | Which world. Null for account-level events. Indexed |
| `payload`       | JSON, nullable              | Event-specific details (see below)              |
| `created_at`    | TIMESTAMP                   | Defaults to now. Indexed                        |

`payload`, not `metadata`: SQLAlchemy reserves `metadata` on every declarative model, so a
column attribute with that name will not map.

`user_id` comes from the request's account, or from `keep.account_id` at insert points that
only hold a keep (expedition finalization, day advance, level-ups).

---

## Event Types (16)

### Lifecycle

| event_type_id     | payload                     | Insert point                              |
|-------------------|-----------------------------|-------------------------------------------|
| `account_created` | —                           | `routes/auth.py` `register`               |
| `keep_created`    | `{keep_name}`               | `routes/keeps.py` `create_keep`           |
| `keep_deleted`    | `{keep_name, current_day, keep_id}` | `routes/keeps.py` `delete_keep`; `keep_id` column left null, since the FK would null it once the keep is gone |
| `return_session`  | `{hours_since_last}`        | `routes/auth.py` `login` **and** `refresh` |

`return_session`: a gap of one hour or more since the user's last activity. "Last activity"
is the most recent `created_at` in `player_events` for that user, or the account's
`created_at` if they have none. Access tokens expire after 30 minutes and the client renews
them silently through `refresh` (the refresh token lasts 7 days and is re-issued on every
refresh, so a player stays signed in unless they are away a full week). Anyone returning
after an hour therefore necessarily passes through `refresh` or `login`; those two handlers
are the only insert points and no per-request check is needed. `refresh` also fires on every
30-minute rollover during play, so the one-hour gap test is what keeps mid-session refreshes
out.

### Core loop — parties and expeditions

| event_type_id          | payload                                                              | Insert point                                    |
|------------------------|----------------------------------------------------------------------|-------------------------------------------------|
| `party_formed`         | `{party_name, member_count}`                                         | `routes/parties.py` `create_party`, which takes the member ids: Form Party is one request, so the party is whole or not at all and the count is real |
| `expedition_started`   | `{party_name, dungeon_level, is_auto_delve}`                         | `routes/expeditions.py` `launch_expedition` and `_auto_launch_expedition` |
| `expedition_decision`  | `{choice, was_auto, trigger_type, dungeon_level, party_name}`        | `routes/expeditions.py` `make_expedition_choice` — every choice the player submits, including "let the party decide" (`was_auto`, with `choice` the outcome). Day-advance auto-decide does not log |
| `expedition_completed` | `{party_name, dungeon_level, retreated, loot_gp, xp_gained, deaths}` | `_finalize_expedition` — the one function every completion path reaches |
| `tpk`                  | `{party_name, dungeon_level, adventurers_lost, monster_type, monster_count, party_avg_level}` | `_finalize_expedition`, when every member who went out is in the effective result's `dead_members` |

**`tpk` captures how it happened, on the event, not by reconstruction** (Cody, 2026-09-09):

- `monster_type`, `monster_count`: from the `combat` entry of the log turn in which the last
  member died. The simulator already writes both on every combat result
  (`app/expedition.py`, `resolve_combat`). When deaths span several combats, the wipe is the
  combat that killed the last member; that is the one recorded.
- `party_avg_level`: mean of the party's levels at the time of the wipe, one decimal. Levels
  change only at finalization, so this equals the mean of `base_level` across the simulator's
  party snapshot for that expedition. Compute it before `apply_level_ups` runs.
- `adventurers_lost`: the count.

A TPK also emits one `adventurer_died` per member and one `expedition_completed`; the `tpk`
row is in addition, because it is the sharpest attachment signal the cohort can produce and
must be findable without joining anything.

### Adventurer milestones

| event_type_id           | payload                                                     | Insert point                                  |
|-------------------------|-------------------------------------------------------------|-----------------------------------------------|
| `adventurer_died`       | `{adventurer_name, class, level, dungeon_level, party_name}` | `_finalize_expedition`, per death            |
| `adventurer_levelled`   | `{adventurer_name, class, new_level, first_time}`           | `progression.py` `apply_level_ups` (session via `object_session(adv)`, user via `keep.account_id`) |
| `adventurer_bankrupt`   | `{adventurer_name, class, level, debt_cp}`                  | `routes/game.py` `process_upkeep`, where `is_bankrupt` is set |

`first_time`: true when the new level exceeds `keep.highest_level_achieved` before the
update. `apply_level_ups` already computes this for its popup event; reuse it.

### Economy and buildings

| event_type_id                     | payload                                                            | Insert point                                          |
|-----------------------------------|--------------------------------------------------------------------|-------------------------------------------------------|
| `building_purchased`              | `{building_type, level, cost_gp}`                                  | `routes/buildings.py` `buy_building` and `upgrade_building` (`level` distinguishes them) |
| `adventurer_assigned_to_building` | `{adventurer_name, class, level, building_type, building_level}`   | `routes/buildings.py` `assign_adventurer`             |

### Progression gates

| event_type_id        | payload            | Insert point                                                        |
|----------------------|--------------------|---------------------------------------------------------------------|
| `stairs_discovered`  | `{new_max_level}`  | `_finalize_expedition`, where `keep.max_dungeon_level` is raised    |

### Automation

| event_type_id          | payload                          | Insert point                                    |
|------------------------|----------------------------------|-------------------------------------------------|
| `auto_delve_triggered` | `{party_name, dungeon_level}`    | `_auto_launch_expedition`, first auto-launch for this user only |

Guard the insert with a query for an existing `auto_delve_triggered` row for the user. Every
auto-launch still logs `expedition_started` with `is_auto_delve = true`; this event only
marks the moment a player first handed the loop to the machine.

### Not recorded

- **Adventurer recruited.** Recruitment rolls free every day inside `advance_day`; it is a
  world event, not a player action, and none of the four questions needs it.
- **Day advanced / skip to event.** Too frequent to be worth a row; the expedition events
  carry the game day when it matters.

---

## Implementation

### Helper

One function, called from every insert point:

```python
def log_player_event(
    db: Session,
    event_type: EventType,
    user_id: int,
    keep_id: int | None = None,
    payload: dict | None = None,
) -> None:
    db.add(PlayerEvent(
        event_type_id=event_type.value,
        user_id=user_id,
        keep_id=keep_id,
        payload=payload,
    ))
```

No separate commit. It rides the request's transaction: if the action rolls back, so does
the event, which is correct — if the action did not happen, the event should not exist.

### Migration

One Alembic revision creates both tables, the four indexes, and seeds the 16 `event_types`
rows from `EventType`. Runs on SQLite (local) and Postgres (production) unchanged; the JSON
column is SQLAlchemy's generic `JSON`, which both support.

### Tests

API tests for the insert points that are reachable through `TestClient`: register, create
keep, form party, launch, choose, and one finalization with a death. Assert the row and the
payload keys, not the copy.

---

## The four gate queries

Written now so the schema is known to answer them; the admin command that runs them is
weekend two. Postgres syntax. For SQLite replace `COUNT(*) FILTER (WHERE …)` with
`SUM(CASE WHEN … THEN 1 ELSE 0 END)`.

### One row per player: all four questions at once

```sql
SELECT
    a.username,
    a.created_at                                                                    AS joined,
    MIN(e.created_at) FILTER (WHERE e.event_type_id = 'keep_created')               AS first_keep,
    MIN(e.created_at) FILTER (WHERE e.event_type_id = 'party_formed')               AS first_party,
    MIN(e.created_at) FILTER (WHERE e.event_type_id = 'expedition_started')         AS entered_loop,   -- Q1
    COUNT(*)          FILTER (WHERE e.event_type_id = 'expedition_completed')       AS expeditions,
    COUNT(*)          FILTER (WHERE e.event_type_id = 'return_session')             AS returns,        -- Q3
    MAX(e.created_at) FILTER (WHERE e.event_type_id = 'return_session')             AS last_return,
    MIN(e.created_at) FILTER (WHERE e.event_type_id = 'adventurer_died')            AS first_death,    -- Q4
    MIN(e.created_at) FILTER (WHERE e.event_type_id = 'adventurer_levelled')        AS first_level_up, -- Q4
    COUNT(*)          FILTER (WHERE e.event_type_id = 'tpk')                        AS wipes,
    MAX(e.created_at)                                                               AS last_seen
FROM accounts a
LEFT JOIN player_events e ON e.user_id = a.id
GROUP BY a.id, a.username, a.created_at
ORDER BY last_seen DESC NULLS LAST;
```

`entered_loop` null means Q1 is "no". Everyone with a null `first_keep`, `first_party` or
`entered_loop` shows exactly how far they got before stopping.

### Q2: where did they leave?

The last thing each player did before going quiet, with what it was.

```sql
SELECT DISTINCT ON (e.user_id)
    a.username,
    e.event_type_id AS last_event,
    e.payload,
    e.created_at    AS when_left
FROM player_events e
JOIN accounts a ON a.id = e.user_id
ORDER BY e.user_id, e.created_at DESC;
```

Read with the funnel above: a player whose last event is `keep_created` left before forming
a party; one whose last event is `expedition_started` left before witnessing the return.

### The wipes, in full

```sql
SELECT a.username, e.keep_id, e.created_at,
       e.payload->>'party_name'       AS party,
       e.payload->>'dungeon_level'    AS depth,
       e.payload->>'monster_type'     AS killed_by,
       e.payload->>'monster_count'    AS how_many,
       e.payload->>'party_avg_level'  AS avg_level,
       e.payload->>'adventurers_lost' AS lost
FROM player_events e
JOIN accounts a ON a.id = e.user_id
WHERE e.event_type_id = 'tpk'
ORDER BY e.created_at;
```

### Per-player timeline

For reading one player's whole story once the summary flags them.

```sql
SELECT e.created_at, e.keep_id, e.event_type_id, e.payload
FROM player_events e
JOIN accounts a ON a.id = e.user_id
WHERE a.username = :username
ORDER BY e.created_at;
```

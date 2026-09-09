# Player Events — v0.9.1 Spec

Scope: understand player behavior so we can identify their problems and make
informed product decisions. Not a full analytics pipeline — one table, one
helper, insert calls at the right spots.

---

## Schema

### `event_types`

Lookup table. Varchar PK so joins read like English and new types are a row
insert, not a migration.

| Column        | Type        | Notes              |
|---------------|-------------|--------------------|
| `id`          | VARCHAR PK  | Slug, indexed      |
| `description` | VARCHAR     | Human-readable     |

### `player_events`

One row per event. Narrow table with a JSON metadata column for
event-specific details.

| Column          | Type                        | Notes                                          |
|-----------------|-----------------------------|-------------------------------------------------|
| `id`            | INT PK                      | Auto-increment                                  |
| `event_type_id` | VARCHAR FK → event_types.id | Indexed                                         |
| `user_id`       | INT FK → accounts.id        | Who                                             |
| `keep_id`       | INT FK → keeps.id, nullable | Which world (null for account-level events)      |
| `metadata`      | JSON, nullable              | Event-specific payload (see below)               |
| `created_at`    | TIMESTAMP                   | Defaults to now                                  |

Indexes: `event_type_id`, `user_id`, `keep_id`, `created_at`.

---

## Event Types (16)

### Lifecycle

| event_type_id     | metadata                          | Insert point                  |
|-------------------|-----------------------------------|-------------------------------|
| `account_created` | —                                 | `routes/auth.py` POST /register |
| `keep_created`    | `{keep_name}`                     | `routes/keeps.py` POST /keeps   |
| `keep_deleted`    | `{keep_name, current_day}`        | `routes/keeps.py` DELETE /keeps/{id} |
| `return_session`  | `{hours_since_last}`              | Login or first authenticated request after 1+ hour gap |

`return_session`: any gap in activity of 1 hour or more. Track the hours
since last activity in the metadata. "Activity" = the most recent
`created_at` in `player_events` for that user, or the account's
`created_at` if they have no events yet.

### Core Loop — Parties & Expeditions

| event_type_id          | metadata                                                          | Insert point                         |
|------------------------|-------------------------------------------------------------------|--------------------------------------|
| `party_formed`         | `{party_name, member_count}`                                      | `routes/parties.py` POST /parties    |
| `expedition_started`   | `{party_name, dungeon_level, is_auto_delve}`                      | `routes/expeditions.py` POST /expeditions (and auto-delve launch in game.py) |
| `expedition_decision`  | `{choice, trigger_type, dungeon_level, party_name}`               | `routes/expeditions.py` POST /expeditions/{id}/choose |
| `expedition_completed` | `{party_name, dungeon_level, retreated, loot_gp, xp_gained, deaths}` | Expedition finalization in `routes/expeditions.py` or `game.py` day-advance |
| `tpk`                  | `{party_name, dungeon_level, adventurers_lost}`                   | Inside expedition finalization, when all party members die |

### Adventurer Milestones

| event_type_id           | metadata                                              | Insert point                     |
|-------------------------|-------------------------------------------------------|----------------------------------|
| `adventurer_died`       | `{adventurer_name, class, level, dungeon_level, party_name}` | Expedition finalization, per death |
| `adventurer_levelled`   | `{adventurer_name, class, new_level, first_time}`     | `progression.py` apply_level_ups |
| `adventurer_bankrupt`   | `{adventurer_name, class, level, debt_cp}`            | Upkeep processing in game.py     |

`first_time`: true when the new level exceeds `keep.highest_level_achieved`.

### Economy & Buildings

| event_type_id                    | metadata                                                  | Insert point                          |
|----------------------------------|-----------------------------------------------------------|---------------------------------------|
| `building_purchased`             | `{building_type, level, cost_gp}`                         | `routes/buildings.py` POST /buildings/buy and POST /buildings/{id}/upgrade |
| `adventurer_assigned_to_building`| `{adventurer_name, class, level, building_type, building_level}` | `routes/buildings.py` POST /buildings/{id}/assign |

### Progression Gates

| event_type_id        | metadata            | Insert point                                   |
|----------------------|---------------------|-------------------------------------------------|
| `stairs_discovered`  | `{new_max_level}`   | Expedition finalization, when max_dungeon_level increases |

### Automation

| event_type_id          | metadata                        | Insert point                          |
|------------------------|---------------------------------|---------------------------------------|
| `auto_delve_triggered` | `{party_name, dungeon_level}`   | Auto-delve launch path in game.py day-advance |

First auto-delve launch only: guard the insert with a check for whether
this user already has an `auto_delve_triggered` event.

---

## Implementation Notes

### Helper function

One function, call it from every insert point:

```python
def log_player_event(db, event_type_id, user_id, keep_id=None, metadata=None):
    db.add(PlayerEvent(
        event_type_id=event_type_id,
        user_id=user_id,
        keep_id=keep_id,
        metadata=metadata,
    ))
```

No separate commit — it piggybacks on the request's existing transaction.
If the request rolls back, the event rolls back too. That's correct: if the
action didn't happen, the event shouldn't exist.

### Seed data

The Alembic migration should insert all 16 event type rows into
`event_types`. Adding new types later is just a new migration with an
INSERT — no schema change needed.

### Admin query (from the roadmap)

> "Did they enter the core loop, where did they leave, did they return,
> did they reach a death or a level-up?"

```sql
SELECT
    a.username,
    e.event_type_id,
    e.keep_id,
    e.metadata,
    e.created_at
FROM player_events e
JOIN accounts a ON a.id = e.user_id
WHERE e.event_type_id IN (
    'account_created', 'keep_created', 'party_formed',
    'expedition_started', 'expedition_completed',
    'adventurer_died', 'adventurer_levelled', 'tpk',
    'return_session'
)
ORDER BY a.username, e.created_at;
```

For a per-user summary:

```sql
SELECT
    a.username,
    COUNT(*) FILTER (WHERE e.event_type_id = 'expedition_started') AS expeditions,
    COUNT(*) FILTER (WHERE e.event_type_id = 'expedition_completed') AS completions,
    COUNT(*) FILTER (WHERE e.event_type_id = 'adventurer_died') AS deaths,
    COUNT(*) FILTER (WHERE e.event_type_id = 'adventurer_levelled') AS levelups,
    COUNT(*) FILTER (WHERE e.event_type_id = 'tpk') AS tpks,
    COUNT(*) FILTER (WHERE e.event_type_id = 'return_session') AS return_sessions,
    MAX(e.created_at) AS last_seen
FROM player_events e
JOIN accounts a ON a.id = e.user_id
GROUP BY a.username
ORDER BY last_seen DESC;
```

These run against Postgres. SQLite doesn't support FILTER — for local dev,
use SUM(CASE WHEN ... THEN 1 ELSE 0 END) instead.

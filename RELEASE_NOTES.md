# v0.9.1 — Safe to Invite

Ready for the first invited players: errors are reported, player actions are recorded, feedback has a form, and the combat and XP bugs found while measuring balance are fixed.

## Combat

- **Dead adventurers no longer fight.** A manual launch reused a cached simulator party keyed on its first member, so a relaunch fought with the roster, HP, levels and items from that party's first launch, the dead included. Every launch now simulates the current roster
- **Parties break and run**: party morale is 7, down from 11, which failed only on a 12. A routed party still gets its potion revives and Cleric heals
- **Armor is damage reduction**: each hit taken does the armor's bonus less damage, to a floor of 0; rings count as armor. The temporary hit points granted at launch are gone
- **A magic weapon adds to to-hit and damage only**, per OSE. It no longer raises hit dice, cures, revivals, turn attempts or spells, and class charges follow true level
- **The Training Grounds' to-hit bonus reaches combat.** The simulator had been overwriting it with the class's own
- **Number appearing trimmed** for the nine depth-1 monsters killing one or more adventurers per fight: Wolf 1d3, Halfling 2d4, Kobold 2d4, Troglodyte 1d3, Sprite 2d4, Giant Gecko 1, Fire Beetle 1d6, Killer Bee 1d8, Rock Baboon 1d3

## XP

- **XP goes to those who come home**: everything a run earned in the turns actually played is one pool, split evenly among the survivors. The dead take nothing; a wipe earns nothing
- **A fled fight pays for the monsters killed before running**, and nothing for the rest
- **Buildings grant XP**: each standing building gives +10% expedition XP to the classes it serves, stacking across buildings. Recruitment is now a flat rate for every class

## Feedback

- **In-game feedback form** from the sidebar footer on every screen and from the login and keep-select pages: a 4-point importance scale, a receipt line and a per-session counter. Signed-in submissions carry the account and keep
- **Buy Me a Coffee** chip in the sidebar footer and on the auth pages
- The sidebar footer is pinned; only the notification feed scrolls

## Expedition Views

- **Healing per member**: summary rows show damage taken, HP healed and revivals beside HP, so a loss next to full health adds up. The event modal's This Event table shows healing received that turn
- **Casualties in a completed summary show the damage they took**, not zero
- **The round log plays back in resolution order**: turn undead, spells, each side's attacks and morale checks as they resolved, with post-combat healing in the last round fought. Older expeditions still render
- **Every adventurer named in an expedition view opens their sheet**: summary rows, event popup rows, names in the log, and the decision page, which now lists the party with class, level and HP
- **The completed summary lists magic items found**, with who carries them

## Character Sheet

- **Items say what they do**, printed under each item
- **XP bar reads total XP against the next threshold**; the fill shows progress within the level

## Dashboard & Village

- **The Village states every effect**: what each building delivers now beside its per-unit rate ("+2" next to "+1 each"), free slots, and the XP bonus. Building copy lives in the building data
- **Village sits under Unassigned Adventurers, beside Parties**, so assigning to a building is a drag between neighbours. Two columns hold down to a 1181px viewport, then stack Unassigned, Parties, Village
- **Adventurer rows line up in columns** on the Dashboard, Parties, Party Formation and Delve screens. Names, XP and wealth wrap rather than truncate
- **Drag-and-drop is optimistic** and dashboard data is prefetched; a failed placement returns the adventurer to its slot
- **Auto-delve is one checkbox** on Parties and the Dashboard party cards, and "Auto-delve to this level" on the Delve screen
- Dashboard XP reads "0 / 2000 XP"; Temple reads "HP / day while healing"
- The dashboard hint bar is gone; unbuilt Village cards no longer reserve space for stats

## Tavern

- **The Roster shows every living adventurer.** It fetched the 100 oldest adventurers of any status and filtered them client-side, which left an older keep's Roster empty. Newest first
- **Graveyard and Debtor's Prison get search, class filter and sort**, including Died and Bankrupted, newest first

## Sessions

- **The session is checked before the first paint**: no dashboard flash for a signed-out or expired session
- A reload more than 30 minutes after the last request no longer logs out a player whose refresh token is still valid
- A mid-session 401 routes to login without a full reload

## Observability

- **Sentry** on backend and frontend, errors only, tagged with the build string and environment. API 5xx responses and failed requests are reported even where the UI catches them
- **`player_events`**: one row per player action across 16 event types, from account creation to party wipe. A wipe records the monster, how many, and the party's average level
- `scripts/gate_queries.py` answers the v1.0 gate: per-account core-loop summary, where each player left, every TPK, and one account's timeline. Runs on SQLite or Postgres
- `scripts/balance_stats.py` (`--keep`, deaths by depth) and `scripts/number_appearing_sweep.py`

## Technical

- Alembic migrations for `player_events` with its `event_types` lookup (`d5e1f2a3b4c6`) and `feedback` (`e6f2a3b4c5d7`)
- Python deps in a `[project]` table with a real `uv.lock`; `requirements.txt` removed. Dockerfile on `python:3.13-slim` with `uv sync --frozen --no-dev`
- New env: `SENTRY_DSN` and `APP_ENV` on the server; `VITE_SENTRY_DSN` wherever the frontend is built
- `python-multipart` 0.0.31 (four DoS advisories); frontend `npm audit` clean (vite 6.4.3, postcss 8.5.28)
- Test suite runs against Postgres through `DATABASE_URL`; fixed the FK cycle and unseeded `event_types` that SQLite had hidden. Restore from backup drilled
- Form Party is one request; game data is read as UTF-8 on every platform
- 108 tests passing

---

# v0.9 — The Polish Release

A full pass over the interface: a rebuilt expedition event modal, a visible economic loop, a complete character sheet, and level-ups that land the moment they are earned.

## Expedition Event Modal

- **Event line**: typed badge and narrative, with the decision buttons at the top
- **"This Event" table**: per-adventurer damage and HP after
- **"Expedition So Far" ledger**: damage dealt and taken per member, HP bars, spell and cure columns, totals row, banked loot
- **Nested expedition log**: three-level tree (turn → event → round), now also used by the Summary view
- **Combat deaths name their killer** in the event message
- **"Rest in Peace"** after a party wipe returns to the Dashboard instead of the wiped party's summary

## Economic Loop

- **Upkeep Day modal**: treasury delta and Collect first, then the per-adventurer ledger — paid, sacrificed items, debtor's prison. Treasury and roster hold until Collect; the feed keeps clickable receipts that reopen the ledger read-only
- **Sidebar forecast**: persistent upkeep line under Treasury plus a red at-risk list, both opening a read-only forecast modal with the day-30 projection and per-payer shortfalls
- **Upkeep simplified**: everyone pays on the day, in the dungeon or not; only building staff are exempt. Someone away and short pays what they have and settles the rest on return, loot included. Debtor's prison only at the gate. Deferred upkeep removed
- **Village rebuilt around numbers**: per-unit stat values from config, tier-delta column, slot chips with level requirements, click-to-assign listing only eligible adventurers, affordability-styled Build buttons
- **Building costs cut to 10%**: 50 / 250 / 1250gp, down from 500 / 2500 / 12500

## Character Sheet

- Full sheet — stats, XP bar, expedition history, items, upkeep — opened by **every adventurer name in the game**
- **One d20-style TO-HIT** replaces THAC0 and ATK. HD, LVL, WEALTH, UPKEEP and equipment carry help text
- **Every unlocked class ability is listed** with its uses per expedition. Cleric abilities match the simulation: Turn Undead, Revive, Cure Light Wounds, gated behind level 2. One spell: Sleep
- **Combat log**: reads "roll + bonus To-Hit vs Armor Class" with an ascending AC. Heals name the healer, potion and Cleric revives are logged with their source, scroll casts are marked, round summaries read "N attacks · N hits · N dmg", and Damage Healed credits the healer

## Level-Ups

- An adventurer **levels the instant expedition XP is credited**, not at end of day
- **Every level-up raises a popup**, not only a new record for the keep. Several on one day queue and show one at a time
- Level-ups also appear in the sidebar feed
- Level-up popups wait behind a pending decision or the Upkeep ledger rather than stacking on them

## Links

- **Any notification or popup naming an adventurer links to their sheet.** Events carry the ids of everyone they name
- **A party's status badge on the Dashboard is a link**: Ready or Healing opens Launch Expedition, On Expedition opens that expedition's summary

## Witnessed State

State no longer changes before the event that caused it has been seen.

- The dashboard holds its refresh until a queued event popup is on screen
- Resource counters show the launch snapshot until a turn is witnessed
- Phase totals, deaths and stairs stay hidden behind the same gate
- The in-progress summary replays only witnessed turns, not the pre-simulated future
- Day-advance no longer bumps the expedition version in the store

## Parties

- **Dead adventurers leave their party** when an expedition resolves, freeing its slots; an empty party stands until end of day, then disbands
- **Disbanded parties keep their row and their expeditions**, so the Expeditions tab keeps the history
- Return copy reads "*Party* brought back X (Y each)"; retreat and return notifications name the party
- Dashboard parties expand independently
- **Early retreats report the day the party came home**: the Summary shows PLANNED against ACTUAL, and the Expeditions list and detail view no longer show the abandoned plan
- Fixed a party wipe leaving phantom survivors

## Smaller Things

- Dwarves may train at the Training Grounds
- Character sheet modal stacks above other modals
- Tier II+ building UI hidden; the data and the upgrade endpoint stay
- `ADMIN_CONSOLE_OPEN` env flag opens the admin console to any signed-in account; unset, behaviour is unchanged
- Building stat lines read "per assigned"
- Upkeep table money columns widened, values no longer wrap

## Technical

- `GameEvent` gains a structured `data` payload and an `adventurers` list of everyone a message names
- `/dashboard/stats` gains `upkeep_forecast`; the buildings payload gains `current_stats` / `next_stats`
- Alembic migration for the party `disbanded` column
- Shell scripts pinned to LF, Python pinned to 3.13
- API regression tests for retreat dates and level-up timing; 76 passing

---

# v0.8.1

## Stairs Rework

- **Always-popup stairs**: Stairs discovery completely decoupled from the decision-point system. Now fires at expedition finalization as a dedicated `stairs_discovered` event — the player ALWAYS gets a disruptive popup, regardless of auto-decide settings.
- **Rebalanced chance**: 1.5% per turn at the deepest unlocked level, +1% per Dwarf in the party.
- **Skip-to-event awareness**: "Skip to Event" now stops on stairs discovery.

## Party Wipe

- Wiped parties (all members dead or bankrupt) are now hidden from the dashboard and Parties view instead of lingering as "Empty".
- Party count reflects only active parties.

## Admin

- `test stairs` command simplified — directly unlocks next level and fires a popup event for testing.

---

# v0.8 — The Monster Release

## Combat & Balance

- **OSE Hit Points**: Adventurers now roll their class hit die per level-up (Fighter d8, Cleric/Elf/Halfling d6, Magic-User d4) instead of a flat formula. HD progression unchanged.
- **OSE Treasure Tables**: Loot now follows tiered treasure tables — silver always, gold at 50%, gems/jewelry/magic items by percentage per dungeon tier.
- **Spell HD Limits**: Base spells only insta-kill monsters with HD ≤ caster level + 3. Scrolls still insta-kill anything.
- **100 Monsters**: Expanded the bestiary from 18 to 100 monsters covering the full OSE dungeon encounter tables.
- **Magic Item Variety**: Added rings, named scrolls, and named potions to the magic item pool.

## Dungeon

- **Stairs Discovery**: Stairs are no longer guaranteed every frontier expedition. Now a 1% chance per turn (Dwarves add +0.5% per turn). One staircase max per expedition per level.
- **Random Dungeon Level Names**: Each world generates unique level names on creation ("The Ashen Crypts", "The Howling Warrens", etc.) so deeper levels feel like real discoveries.

## Auto-Delve Hardening

- TPK cleanup: ghost parties with dead members get auto-delve disabled automatically.
- `auto_delve_level` clamped to valid range (≥ 1, ≤ max unlocked).
- Neither "When Healed" nor "When Full" checked = party does not auto-delve.
- Stairs events always prompt the player, even with auto-decide enabled.

## Admin Tools

- **Metrics Panel**: Type `metrics` in the admin console to show a "Metrics" button in the header. Click it to view per-level balance data: runs, avg gold, avg XP, deaths/run, total deaths.
- **Test Stairs**: Type `test stairs` to force a stairs popup on any active expedition for debugging.
- **Help**: Type `help` to see all available admin commands.

## Technical

- Per-class config system (`app/class_config.py`, `app/data/classes.json`) for hit dice, THAC0, saves, and XP tables.
- Alembic migration for `dungeon_level_names` JSON column on Keep.
- Vite proxy config updated for `/metrics` endpoint.
- Spell casting refactored into `_try_fire_spell()` to eliminate duplicate code blocks.

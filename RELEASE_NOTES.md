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

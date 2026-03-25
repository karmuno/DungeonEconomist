# Building System Overhaul — Detailed Implementation Plan

This document describes a comprehensive rework of all three existing buildings (Temple, Training Grounds, Library) and the addition of a new Dwarf building (Smithy/Forge). Each building now has **class-specific, level-gated powers** with distinct slot counts and minimum adventurer levels per tier.

---

## Design Overview

### Slot & Level Requirements Per Tier

| Building | Tier I Slots × Min Lvl | Tier II Slots × Min Lvl | Tier III Slots × Min Lvl |
|---|---|---|---|
| Temple (Cleric) | 3 × Lvl 2 | 2 × Lvl 6 | 1 × Lvl 9 |
| Training Grounds (Fighter) | 3 × Lvl 2 | 2 × Lvl 6 | 1 × Lvl 9 |
| Library (M-U) | 3 × Lvl 1 | 2 × Lvl 6 | 1 × Lvl 9 |
| Smithy (Dwarf) | 2 × Lvl 2 | 1 × Lvl 6 | — (max level 2) |

### Cross-Class Building Eligibility

- **Elves** can be assigned to **Library** (M-U building) or **Training Grounds** (Fighter building)
- **Halflings** can be assigned to **Training Grounds** (Fighter building)

---

## Building Power Details

### Temple (Cleric Building)

**Tier I — Shrine** (3 slots, Lvl 2 Clerics)
- **Passive Healing:** Each assigned Cleric grants +1 HP/day healing to all unassigned, non-expedition adventurers
- *Already partially implemented* — `_get_temple_healing_bonus()` in `routes/game.py` counts assigned clerics

**Tier II — Church** (2 slots, Lvl 6 Clerics)
- **Healing Potion Crafting:** When an adventurer returns from expedition, there is a small chance (e.g. 10% base per living member) they spend 100gp to buy a Healing Potion from the temple
  - This is a **magic item** (`item_type: "potion"`) — acts as a one-time auto-resurrection consumable
  - Only 1 potion can be carried per adventurer
  - Chance doubles with 2 clerics stationed (e.g. 10% → 20%)
  - Potion is consumed when the adventurer dies during expedition → they come back at 1 HP

**Tier III — Cathedral** (1 slot, Lvl 9 Cleric)
- **Resurrection on Return:** Upon return from expedition, the highest-level dead party member is brought back to life at half their max HP
  - Processed during `_finalize_expedition()` before loot split

---

### Training Grounds (Fighter Building)

**Tier I — Training Grounds** (3 slots, Lvl 2 Fighters)
- **To-Hit Bonus:** All fighters (including Dwarves, Halflings, Elves) in the keep's parties get +1 to-hit per stationed Lvl 2 Fighter
  - Currently implemented as a flat `level` boost via `_get_combat_bonus()`. Needs rework to apply as an actual THAC0 modifier rather than inflating effective level

**Tier II — Military Camp** (2 slots, Lvl 6 Fighters)
- **Damage Bonus:** +1 damage per stationed Fighter to all party members in combat
  - New mechanic — damage bonus applied in `_do_attack()` or passed through expedition setup

**Tier III — Castle** (1 slot, Lvl 9 Fighter)
- **Morale Penalty:** Monsters check morale at -2
  - Modifier applied in `_morale_check()` during combat resolution

---

### Library (Magic-User Building)

**Tier I — Library** (3 slots, Lvl 1 M-Us)
- **Magic Item Discovery:** Small chance per adventurer per expedition of discovering class-appropriate magic items:
  - Fighters → weapons & armor
  - Clerics → armor & healing potions
  - M-Us → scrolls (each scroll = 1 extra spell use)
  - Represents M-Us "identifying" items from junk
  - Chance scales with number of M-Us stationed

**Tier II — University** (2 slots, Lvl 6 M-Us)
- **Scroll Crafting:** Similar to Cleric healing potion at Tier II — on return, there's a chance adventurers (M-Us and Elves) buy a scroll
  - Scroll is a magic item that grants +1 spell use for one expedition
  - Chance doubles with 2 M-Us

**Tier III — Wizard's Tower** (1 slot, Lvl 9 M-U)
- **Craft Artifact:** Costs 1000gp from treasury, doubles a M-U's spell uses
  - Can be purchased multiple times; effects stack
  - Implemented as a special magic item (`item_type: "artifact"`) with a `spell_multiplier` field

---

### Smithy (Dwarf Building) — **NEW**

**Tier I — Smith** (2 slots, Lvl 2 Dwarves)
- Two distinct crafting modes based on which slot is filled:
  - **Slot A — Craft Magic Weapon:** Chance per expedition to produce a +1 weapon for a fighter-type party member
  - **Slot B — Craft Magic Armor:** Chance per expedition to produce +1 armor for a party member
- Each slot independently runs its craft check

**Tier II — Forge** (1 slot, Lvl 6 Dwarf)
- **Masterwork Craftsmanship:** When the Smithy produces an item, there's a random chance it's +2 or +3 instead of +1
  - Only applies if Tier I has produced an item — Tier II enhances the quality

---

## Implementation Breakdown

### 1. Data Layer — `buildings.json`

Rewrite all four building configs with correct slot counts, min levels, and new bonus descriptors:

```json
{
  "temple": {
    "class": "Cleric",
    "allowed_classes": ["Cleric"],
    "names": ["Shrine", "Church", "Cathedral"],
    "costs": [500, 2500, 12500],
    "max_assigned": [3, 2, 1],
    "min_adventurer_level": [2, 6, 9],
    ...
    "level_bonuses": {
      "1": { "healing_per_assigned": 1 },
      "2": { "healing_potion_chance_per_cleric": 0.10 },
      "3": { "resurrect_highest_dead": true }
    }
  },
  "training_grounds": {
    "class": "Fighter",
    "allowed_classes": ["Fighter", "Elf", "Halfling"],
    "names": ["Training Grounds", "Military Camp", "Castle"],
    "costs": [500, 2500, 12500],
    "max_assigned": [3, 2, 1],
    "min_adventurer_level": [2, 6, 9],
    ...
    "level_bonuses": {
      "1": { "to_hit_per_assigned": 1 },
      "2": { "damage_per_assigned": 1 },
      "3": { "monster_morale_penalty": -2 }
    }
  },
  "library": {
    "class": "Magic-User",
    "allowed_classes": ["Magic-User", "Elf"],
    "names": ["Library", "University", "Wizard's Tower"],
    "costs": [500, 2500, 12500],
    "max_assigned": [3, 2, 1],
    "min_adventurer_level": [1, 6, 9],
    ...
    "level_bonuses": {
      "1": { "magic_item_discovery_per_assigned": 0.03 },
      "2": { "scroll_craft_chance_per_mu": 0.10 },
      "3": { "craft_artifact_cost": 1000 }
    }
  },
  "smithy": {
    "class": "Dwarf",
    "allowed_classes": ["Dwarf"],
    "names": ["Smith", "Forge"],
    "costs": [500, 2500],
    "max_assigned": [2, 1],
    "min_adventurer_level": [2, 6],
    "retire_level": 9,
    "recruitment_bonus": true,
    ...
    "level_bonuses": {
      "1": { "craft_weapon_slot": true, "craft_armor_slot": true },
      "2": { "masterwork_chance": 0.15 }
    }
  }
}
```

### 2. Model Changes — `models.py`

- Expand `MagicItem.item_type` to support `"potion"`, `"scroll"`, and `"artifact"` in addition to `"weapon"` and `"armor"`
- Add `MagicItem.consumable` boolean (potions and scrolls are consumed on use)
- Add `MagicItem.spell_multiplier` integer (for artifacts; defaults to 0)
- No schema migration needed if using SQLite with dynamic typing, but add a proper Alembic migration for correctness

### 3. Building Logic — `buildings.py`

- Add `get_allowed_classes()` helper that reads `allowed_classes` from config (falls back to `[config["class"]]`)
- Cumulative bonus getters that aggregate across all building levels:
  - `get_total_to_hit_bonus(keep, db)` — count Tier I training grounds assigned
  - `get_total_damage_bonus(keep, db)` — count Tier II training grounds assigned
  - `get_monster_morale_penalty(keep, db)` — -2 if Tier III fighter stationed
  - `get_healing_potion_chance(keep, db)` — per-cleric chance from Tier II temple
  - `get_resurrect_on_return(keep, db)` — bool, Tier III temple
  - `get_magic_discovery_chance(keep, db)` — per-MU from Tier I library
  - `get_scroll_craft_chance(keep, db)` — per-MU from Tier II library
  - `has_artifact_crafting(keep, db)` — bool, Tier III library
  - `get_smithy_crafting(keep, db)` — returns which crafting slots are active
  - `get_masterwork_chance(keep, db)` — Tier II smithy enhancement chance

### 4. Combat Integration — `expedition.py`

- Accept `to_hit_bonus` and `damage_bonus` parameters in party member dicts
- Apply `to_hit_bonus` in `_do_attack()` by subtracting from THAC0 (lower THAC0 = easier to hit)
- Apply `damage_bonus` in `_do_attack()` by adding to damage rolls
- Accept `morale_penalty` for monster morale checks in `_morale_check()`
- Support potion auto-revive: if a party member dies and has a potion magic item, consume it and set HP to 1

### 5. Expedition Launch — `routes/expeditions.py`

- Pass building bonuses into simulator party member dicts:
  - `to_hit_bonus` from Training Grounds Tier I
  - `damage_bonus` from Training Grounds Tier II
  - `morale_penalty` from Training Grounds Tier III
  - Mark members carrying potions/scrolls with their item data

### 6. Expedition Return — `_finalize_expedition()` in `routes/expeditions.py`

- **Temple Tier III:** Before processing deaths, check for Tier III Cathedral. If present, revive the highest-level dead member at half HP
- **Temple Tier II:** After loot split, roll for each living member to see if they purchase a Healing Potion (100gp cost from their personal funds)
- **Library Tier I:** Rework existing magic item discovery to be class-appropriate and scale with each stationed M-U
- **Library Tier II:** Roll for scroll purchases (similar to potion mechanic)
- **Smithy Tier I:** Roll for weapon/armor crafting per active slot
- **Smithy Tier II:** When Tier I produces an item, roll for +2 or +3 upgrade chance

### 7. Assignment Validation — `routes/buildings.py`

- Replace single-class check with `allowed_classes` list check
- Validate Elves can go into Library or Training Grounds
- Validate Halflings can go into Training Grounds

### 8. Artifact Crafting API — `routes/buildings.py` (new endpoint)

- `POST /buildings/{building_id}/craft-artifact` — spends 1000gp from treasury, creates artifact magic item for a specified M-U
  - Requires Tier III Library (Wizard's Tower)
  - Target M-U must be specified in request body
  - Creates `MagicItem(item_type="artifact", spell_multiplier=2)`

### 9. Spell Use Integration

- When building party member dicts for simulation, check for scroll items and artifact items
- Scrolls: add +1 to `spells_remaining`, mark scroll as consumed after expedition
- Artifacts: multiply base `spells_remaining` by artifact multiplier

---

## Resolved Design Decisions

1. **Potion cost:** 100gp from adventurer's personal gold
2. **Scroll cost:** Same as potions — 100gp from adventurer's personal gold
3. **Smithy craft frequency:** On expedition return (same mechanic as healing potions)
4. **Library Tier I discovery chance:** 3% per stationed M-U
5. **Artifact spell doubling:** Doubles base (level-based) spell uses; stacks multiplicatively (2×, 4×, 8×…)
6. **Building upgrade path:** Tier slots are **additive** — existing Tier I adventurers remain stationed when upgrading to Tier II

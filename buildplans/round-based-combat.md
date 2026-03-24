# Build Plan: Round-Based Combat Engine

**Status:** Ready to implement
**Target version:** v0.7 (Class Abilities / Simplified Combat overhaul)
**Replaces:** The single-roll HD-comparison in `app/expedition.py:resolve_combat()`

---

## Overview

Replace the current abstracted combat resolution (one roll, ratio-based outcome) with a proper
OSE-style round-by-round simulation. Each combatant attacks once per HD per round, targeting is
weighted by HD, and the Halfling class gets a free pre-round attack. Clerics turn undead,
Magic-Users cast spells, and morale breaks determine when combat ends.

The expedition turn/encounter system (room discovery, stairs, traps, treasure) is **unchanged**.
Only `resolve_combat()` is being replaced.

---

## Design Spec

### 1. Hit Dice by Class

HD determines: number of attacks per round, HP rolls for new characters, and target weight in
bag-of-stones selection.

| Class | HD per Level | Formula |
|---|---|---|
| Fighter | 1 per level | `level` |
| Dwarf | 1 per level | `level` |
| Halfling | 1 per level | `level` |
| Elf | 1 per level | `level` (gets spells too — see §7) |
| Cleric | 1 per 2 levels | `max(1, level // 2)` |
| Magic-User | 1 per 3 levels | `max(1, level // 3)` |

All HP rolls use **d6 per HD**. All attacks deal **d6 damage**. (Update `progression.py`
`HP_GAIN_BY_CLASS` to use average d6 = 3.5 for all classes; existing stored HP is untouched.)

### 2. Attacks Per Round

Each combatant makes **one attack per HD** per round. Fractional monster HD round down, minimum 1.

```
Fighter L3     → 3 HD → 3 attacks/round
Cleric L4      → 2 HD → 2 attacks/round
Magic-User L6  → 2 HD → 2 attacks/round
Goblin (0.5 HD) → 1 attack/round
Orc (1 HD)     → 1 attack/round
Troll (6 HD)   → 6 attacks/round
```

### 3. Target Selection (Bag of Stones)

Attacks are distributed randomly among living opponents. Each living target contributes HD
"stones" to the bag; one stone is drawn per attack.

```python
def pick_target(targets):
    """targets: list of dicts with 'hd' key"""
    bag = []
    for t in targets:
        bag.extend([t] * max(1, int(t['hd'])))
    return random.choice(bag)
```

A Fighter with 3 HD is targeted 3× as often as an uninjured 1 HD Cleric. Monsters are targeted
proportionally too.

### 4. Attack Roll (THAC0 / Descending AC)

**Hit if:** `d20 >= THAC0 - target_AC`

Ties hit (i.e., `>=`, not `>`).

#### PC THAC0

| Class | L 1–3 | L 4–6 | L 7–9 | L 10+ |
|---|---|---|---|---|
| Fighter | 19 | 17 | 14 | 12 |
| Dwarf | 19 | 17 | 14 | 12 |
| Halfling | 19 | 17 | 14 | 12 |
| Elf | 19 | 17 | 14 | 12 |
| Cleric | 19 | 17 | 14 | 12 |
| Magic-User | 19 | 19 | 17 | 17 |

*Cleric detail: levels 1–4 → 19, 5–8 → 17, 9+ → 14.*

**Fighter Level 1 bonus:** +1 to-hit (attack roll +1 at level 1 only; no bonus at L2+).

#### Monster THAC0

```python
def get_monster_thac0(hit_dice: float) -> int:
    return max(10, 20 - int(hit_dice))
```

#### Default AC (Descending)

- **Adventurers:** AC 7 (equivalent to leather armor; no armor tracking in current system)
- **Monsters:** Per `monsters.json` `ac` field (see §10). Default if missing: 9 (unarmored).

### 5. Round 0 — Halfling Pre-Round

Before Round 1 initiative is rolled, all **living Halflings** in the party execute a full attack
round (HD attacks, normal to-hit rolls, d6 damage). Monsters do **not** attack in Round 0.

If all monsters are killed in Round 0, combat ends immediately. No XP check for morale — they're
all dead.

### 6. Round Structure (Round n ≥ 1)

```
A. Roll initiative: party rolls 1d6, monsters roll 1d6.
   - Higher wins. Ties = simultaneous (both sides attack before deaths are applied).
B. Winning side attacks (all living combatants, each makes HD attacks).
C. Losing side attacks (all combatants who were alive at start of step B, including
   those who died during B — they got their attacks in before falling).
D. Death check: if any combatant died in B or C, that side rolls morale (see §9).
E. Continue check:
   - If both sides have living combatants AND both passed morale → Round n+1.
   - Otherwise: combat ends. Grant XP for monsters killed or fled.
```

**Tie initiative:** Both sides attack "simultaneously." Process B and C without removing
casualties between them (collect all damage, then apply deaths, then check morale).

### 7. Cleric: Turn Undead

The cleric has `level` turn attempts per expedition (e.g., a level 3 Cleric has 3 total for
the whole expedition, spent across encounters).

**Combat behavior:** If the party faces undead AND the cleric has attempts remaining AND can
turn at least one of the undead types present, the Cleric turns instead of attacking that round.
If ALL undead present are too powerful to turn (all "—"), the Cleric attacks normally.

**Turn resolution:** For each undead group, consult the table. T = auto-turn (no roll), D =
auto-destroy. Otherwise, roll 2d6 >= threshold to turn. In all cases, "turned" = **destroyed**
(removed from combat, counts for XP as if killed).

**OSE Turn Undead Table (2d6 roll needed; T = auto, D = destroy, — = cannot):**

| Cleric Level → | 1  | 2  | 3  | 4  | 5  | 6  | 7  | 8+ |
|---|---|---|---|---|---|---|---|---|
| ≤1 HD monster  | 7  | T  | T  | D  | D  | D  | D  | D  |
| 2 HD monster   | 9  | 7  | T  | T  | D  | D  | D  | D  |
| 3 HD monster   | 11 | 9  | 7  | T  | T  | D  | D  | D  |
| 4 HD monster   | —  | 11 | 9  | 7  | T  | T  | D  | D  |
| 5 HD monster   | —  | —  | 11 | 9  | 7  | T  | T  | D  |
| 6 HD monster   | —  | —  | —  | 11 | 9  | 7  | T  | T  |
| 7+ HD monster  | —  | —  | —  | —  | 11 | 9  | 7  | T  |

One turn attempt is spent whether or not the roll succeeds.

### 8. Cleric: Post-Combat Revival

Clerics of **level 2+** may revive dead party members immediately after combat ends.

- Capacity: `level // 2` revivals per expedition total (e.g., L4 cleric → 2 revivals).
- Revived adventurer returns with **1 HP** (marked as alive, sets `current_hp = 1`).
- Cannot revive if the Cleric is dead.
- Revived members can fight in subsequent encounters that same expedition.
- This does **not** consume a turn attempt.

### 9. Magic-User: Expedition Spell

The Magic-User has `level` spell uses per expedition.

**Combat behavior:** At the **start** of each combat (before Round 0), if the MU has spells
remaining, roll 1d6. On **4, 5, or 6**, the MU casts their spell. The spell **instantly destroys
all living monsters** in the room. Combat does not proceed; XP is awarded as if all monsters were
killed. Deduct 1 spell use.

If the roll is 1–3, the MU fights normally for this encounter.

**Spell names by level** (cosmetic only — mechanical effect is always instant-kill):

| Level | Spell Name |
|---|---|
| 1 | Sleep |
| 2 | Hold Person |
| 3 | Fireball |
| 4 | Lightning Bolt |
| 5 | Cloudkill |
| 6+ | Disintegrate |

**Elf spells:** Elves also get `level` spells per expedition. They follow the same MU spell
mechanic (roll 1d6 at combat start, cast on 4+). Elf is dual-class: they have Fighter THAC0
and HD, AND MU spells.

### 10. Morale

**Roll:** 2d6. Pass if result ≤ morale rating (stay and fight). Fail if result > morale (flee).

**Triggers:**
- When the **first** combatant on a side dies in a round.
- When **half** of a side has died (cumulative across all rounds).
- Only one morale check per trigger per side (don't double-check for the same death).

**Morale ratings:**
- Monsters: from `monsters.json` `morale` field (see §11).
- Adventurers: fixed morale of **11** (rarely flee; only on catastrophic losses).

**Fleeing side:** Takes no further damage. Counts as combat end for XP purposes.

### 11. XP Awards

- XP only for monsters **killed** or who **fled** (failed morale).
- If the **party fled**, monsters still alive grant **no XP**.
- Formula (unchanged): `floor(monster_hd) * 100` per individual monster killed or fled.
- Dungeon-level bonus is removed from per-monster XP (simplification).

---

## Demihuman Rules

### Dwarf
Fighter variant. Same HD, THAC0, and attack progression as Fighter.
**Stair discovery:** Dwarves increase the chance of finding stairs down. To compensate, lower
the base stair-discovery probability slightly so the overall rate stays balanced.
*(Stair logic is in expedition room discovery — separate from combat. Note for implementation:
find the stair discovery roll in `app/expedition_events.py` or `app/expedition.py` and add a
Dwarf check.)*

### Elf
Dual Fighter/Magic-User. Gets Fighter HD (1 per level), Fighter THAC0, AND MU spells (1 per
level per expedition). Requires **2× XP per level** (double the `XP_THRESHOLDS` values for Elf
in `progression.py`).

### Halfling (rename from Hobbit)
Fighter variant. Sling specialist. Gets the Round 0 free attack (see §5). Otherwise identical
to Fighter in HD and THAC0. Rename `HOBBIT` → `HALFLING` throughout.

---

## Files to Change

### 1. `app/data/monsters.json`
Add `ac` (descending AC, int), `morale` (int, 2–12), and `is_undead` (bool) to every monster.

Suggested values:

| Monster | HD | AC | Morale | Undead |
|---|---|---|---|---|
| Goblin | 0.5 | 6 | 7 | false |
| Orc | 1 | 6 | 8 | false |
| Skeleton | 1 | 7 | 12 | true |
| Hobgoblin | 1.5 | 6 | 8 | false |
| Zombie | 2 | 8 | 12 | true |
| Ghoul | 2 | 6 | 9 | true |
| Ogre | 4 | 5 | 9 | false |
| Wight | 3 | 5 | 12 | true |
| Werewolf | 4 | 5 | 8 | false |
| Troll | 6 | 4 | 10 | false |
| Wraith | 4 | 3 | 12 | true |
| Owlbear | 5 | 5 | 9 | false |
| Dragon (any) | 9 | 2 | 10 | false |
| Vampire | 7 | 2 | 11 | true |
| Demon Lord | 10 | 0 | 12 | false |

*(Add remaining monsters in the file using similar OSE-appropriate values.)*

### 2. `app/monsters.py`
Add three helper functions:
```python
def get_monster_ac(monster_type: str) -> int: ...
def get_monster_morale(monster_type: str) -> int: ...
def is_monster_undead(monster_type: str) -> bool: ...
```

### 3. `app/expedition.py`
This is the core change. Add/replace:

```python
# New helpers
def get_pc_hd(character_class: str, level: int) -> int: ...
def get_pc_thac0(character_class: str, level: int) -> int: ...
def get_monster_thac0(hit_dice: float) -> int: ...
def pick_target(targets: list[dict]) -> dict: ...  # bag of stones

# Cleric abilities
def cleric_turn_attempt(cleric: dict, monsters: list[dict]) -> list[dict]: ...
    # Returns list of monsters destroyed by turning

# MU ability
def mu_should_cast(mu: dict) -> bool: ...
    # Rolls 1d6, returns True on 4+ if spells_remaining > 0

def get_spell_name(level: int) -> str: ...

# Core combat loop
def resolve_combat(monster_type: str) -> dict: ...  # replaces existing method
    # Internally calls resolve_combat_rounds()

def resolve_combat_rounds(
    party: list[dict],
    monsters: list[dict],
) -> dict: ...
```

Replace the existing `resolve_combat()` method on `Expedition`.

### 4. `app/progression.py`
- Rename `AdventurerClass.HOBBIT` → `AdventurerClass.HALFLING` in `HP_GAIN_BY_CLASS` and
  `CLASS_BONUSES` keys.
- Update Elf XP: double `XP_THRESHOLDS` for Elf (add `ELF_XP_THRESHOLDS` or apply a multiplier
  in `check_for_level_up()`).
- Update `HP_GAIN_BY_CLASS` to use average d6 (3 or 4) for all classes (Fighter stays highest
  since they have more HD).

### 5. `app/models.py`
```python
# Change:
HOBBIT = 'Hobbit'
# To:
HALFLING = 'Halfling'
```

### 6. Alembic Migration
```sql
UPDATE adventurers SET adventurer_class = 'Halfling' WHERE adventurer_class = 'Hobbit';
```
Generate with: `alembic revision --autogenerate -m "rename hobbit to halfling"`
Then manually add the UPDATE statement (autogenerate won't catch the value rename).

### 7. `app/seed_adventurers.py`
Update any `'Hobbit'` → `'Halfling'` class references.

### 8. `frontend/src/` — search and replace
Search for `"Hobbit"` and `'Hobbit'` in all `.ts`, `.vue` files. Replace with `"Halfling"`.
Also update display labels and sprite alt text.

### 9. `app/expedition.py` — Dwarf stair bonus
Find where stair discovery is rolled (currently in room discovery or expedition events).
If Dwarf is in party, increase the stair discovery probability. Reduce base stair probability
slightly to compensate.

---

## Combat Result Schema (return dict from `resolve_combat`)

```python
{
    "outcome": str,           # "Victory", "Party Fled", "TPK", "Mutual Retreat"
    "monster_type": str,
    "monster_count": int,
    "rounds_fought": int,
    "mu_spell_used": str | None,    # spell name if MU cast, else None
    "cleric_turned": bool,          # whether cleric turn was attempted
    "monsters_turned": int,         # count destroyed by turning
    "revived_adventurers": list[str],  # names revived by cleric post-combat
    "hp_lost": int,           # total HP lost by party this combat
    "xp_earned": int,         # 0 if party fled
    "monsters_killed": int,
    "monsters_fled": int,
    "party_fled": bool,
    "round_log": [            # per-round detail for expedition log
        {
            "round": int,
            "initiative_winner": str,  # "party" | "monsters" | "tie"
            "attacks": [
                {
                    "attacker": str,
                    "target": str,
                    "roll": int,
                    "needed": int,
                    "hit": bool,
                    "damage": int,
                    "target_died": bool,
                }
            ],
            "morale_checks": [
                {"side": str, "roll": int, "morale": int, "passed": bool}
            ],
        }
    ],
}
```

---

## Testing (`tests/test_combat.py`)

Write unit tests for:
- `[ ]` Halfling kills all 1-HP monsters in Round 0 — combat ends without Round 1.
- `[ ]` MU casts sleep — all monsters destroyed, no rounds fought, correct XP.
- `[ ]` Cleric turns skeleton (L1 vs 1 HD undead → needs 7) — success and failure cases.
- `[ ]` Cleric cannot turn Vampire (L1 vs 7 HD → "—") — Cleric attacks instead.
- `[ ]` Cleric revives dead ally after combat (L4 cleric, 2 revival capacity).
- `[ ]` Morale failure — party with Fighters vs Goblins (morale 7): goblins flee after loss.
- `[ ]` Fighter L1 +1 to-hit — confirmed roll threshold.
- `[ ]` Fighter L2 — no +1 to-hit.
- `[ ]` Elf gets both Fighter attacks AND spell.
- `[ ]` XP = 0 when party flees.
- `[ ]` XP awarded for monsters fled (failed morale), not just killed.
- `[ ]` Bag-of-stones: 3 HD fighter targeted ~3× as often as 1 HD cleric (statistical test).

---

## Implementation Order

1. Add `ac`, `morale`, `is_undead` to `monsters.json`
2. Add monster helpers in `monsters.py`
3. Add `get_pc_hd()`, `get_pc_thac0()`, `get_monster_thac0()` in `expedition.py`
4. Implement `pick_target()` (bag of stones)
5. Implement `cleric_turn_attempt()`
6. Implement `mu_should_cast()` and `get_spell_name()`
7. Implement `resolve_combat_rounds()` loop (Halfling Round 0, then rounds with initiative)
8. Wire morale checks into round loop
9. Wire post-combat cleric revival
10. Replace old `resolve_combat()` with new version
11. Rename `HOBBIT` → `HALFLING` everywhere (models, progression, seed, frontend)
12. Write and run Alembic migration
13. Update `HP_GAIN_BY_CLASS` and Elf XP multiplier in `progression.py`
14. Write `tests/test_combat.py`
15. Run full test suite; balance-check a sample expedition

---

## Notes & Open Questions

- **Simultaneous initiative ties:** Implemented as: process all attacks before applying deaths.
  A simpler alternative is just re-rolling on ties. Either is fine — pick one and note it.
- **MU cast probability (4+ on d6 = 50%):** May be too aggressive for high-level MUs with many
  spells. Could use `1/remaining_combats_estimate` instead. Start with 4+ and playtest.
- **Adventurer morale 11:** Means adventurers flee on a roll of 12 (double-6). That's ~3% per
  check. Feels right for heroes — they will occasionally panic and run.
- **Cleric revival HP:** 1 HP keeps things tense. Could also be `1d6`. Start with 1 HP.
- **Fractional monster HD:** A 0.5 HD Goblin gets 1 attack (minimum). Treat all HD < 1 as 1 HD
  for attack count purposes.
- **Elf dual XP:** Double the XP thresholds for Elves in `progression.py`. This is separate from
  the combat engine but should be implemented in the same PR.

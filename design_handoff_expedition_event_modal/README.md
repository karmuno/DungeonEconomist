# Handoff: Expedition Event modal (Dashboard → Advance Day / Skip to Event)

## Overview

The Expedition Event popup that appears when a day advance produces an `expedition_choice`
event is being replaced. Today it shows a party roster with HP bars, a loose "This Turn"
block, and a centred button row. The new design keeps the same trigger, the same three
choices, and the same modal, but restructures the body into three plainly-labelled parts:

1. **The event** — one narrative line with a type badge (TRAP / COMBAT / TREASURE).
2. **This Event** — a table of only the adventurers this event touched: damage dealt to
   them and the HP it left them at, plus a sentence naming who was untouched.
3. **Expedition So Far** — the full six-row contribution ledger for the whole run
   (HP, dmg dealt, dmg taken, spells left, cures left) with a totals row, a banked line,
   and the existing Expedition Log nested underneath it.

Then the decision block: **Press On / Retreat / You Decide**, each with a permanent
one-line explanation of what the button does (not what will happen).

This is a **minimal change**: no new routes, no new API endpoints required for the
default build (see *Data availability* for the one gap), no changes to the day-advance
flow. In practice it is a rewrite of the body of one component.

## About the design files

`VentureKeep P2 - Dashboard to Event.dc.html` in this bundle is a **design reference
written as a standalone HTML prototype** — a self-contained mock of the Dashboard plus
the new modal, with fake data and its own tiny state machine. It is not production code
and should not be copied into the app. Recreate it in the existing Vue 3 + TypeScript
frontend using that codebase's established patterns (`<script setup>`, Pinia stores,
`ModalDialog.vue`, `ProgressBar.vue`, the CSS custom properties in
`frontend/src/assets/main.css`).

Open the file in a browser. Click **Advance Day** or **Skip to Event** in the left panel
to open the modal. Inside the modal, click **Expedition Log** to expand the log, then
click a turn, an encounter, and a round to walk down the tree.

`VentureKeep P1 - Expedition Event + Summary.dc.html` is the exploration that produced
these decisions (option ids 1a–1h, 2a–2b). Reference only — the P2 file is authoritative.

## Fidelity

**High fidelity.** Colors, type sizes, spacing, borders and radii in the prototype are
final and are all existing tokens from the app's own CSS. Recreate the modal
pixel-for-pixel. The surrounding Dashboard in the prototype is a stand-in for the real
`DashboardView.vue` — do **not** rebuild the Dashboard from it; only the three small
Dashboard-side changes listed under *Dashboard changes* are in scope.

## Files to change

| File | Change |
| --- | --- |
| `frontend/src/components/expeditions/ExpeditionEventModal.vue` | Rewrite the template body + styles. All the real work. |
| `frontend/src/views/DashboardView.vue` | Optional, tiny: the "Recently Returned" card (see below). |
| `frontend/src/views/ExpeditionSummaryView.vue` | Optional, tiny: PLANNED/ACTUAL retreat lines (see below). |

No changes to `SidePanel.vue` (it already owns the trigger, the queue, and
`popupChoice`), `stores/gameTime.ts`, `api/expeditions.ts` or the router.

## Screen: Expedition Event modal

**Purpose.** The player has just advanced time; a party mid-expedition hit an event and
needs a decision. The modal must answer, in order: what just happened, what changed,
what can I do next.

**Container.** Existing `ModalDialog.vue`, scrim `rgba(0,0,0,.75)`, dialog
`background: var(--bg-modal)` (`#111827`), `1px solid #4b5563`, radius `6px`,
`box-shadow: 0 0 40px rgba(0,0,0,.8)`, **width 760px**, `max-height: 88vh`,
`overflow-y: auto`. Body padding `16px`, vertical gap between sections `16px`.

**Header** — sticky, `padding: 12px 16px`, bottom border `1px solid #374151`:
- Left: `Expedition Event` — 15px / 700 / `#4ade80`; then meta 11px `#6b7280`:
  `The Demo Divers · The Lost Sepulchre, Depth 3 · Day 2 of 3`
  (party name · dungeon name, Depth n · Day `days_elapsed` of `duration_days`).
- Right: `×` 15px `#6b7280`, hover `#e5e7eb`. Closing behaves exactly as today
  (`emit('close')` → `viewExpedition()`), including the existing TPK auto-resolve.

### 1. Event line

Row, `gap: 12px`, aligned to top.
- Type badge: 10px / 700 / letter-spacing `.08em`, `padding: 3px 8px`, radius `4px`,
  `color #fbbf24`, `background rgba(251,191,36,.15)`, `border 1px solid rgba(251,191,36,.3)`.
  Text is the event subtype uppercased: `TRAP`, `COMBAT`, `TREASURE`, `STAIRS`.
  Tone by subtype: trap/combat gold, treasure/stairs green (`#4ade80` on
  `rgba(74,222,128,.15)` / `.3` border), TPK red (`#ef4444` on `rgba(239,68,68,.15)`).
- Narrative: 15px / 1.5 / `#e5e7eb`, `text-wrap: pretty`. This is the existing
  `eventMessage` prop, unchanged.

### 2. "This Event" table

Section label: 10px, uppercase, letter-spacing `.12em`, `#6b7280` — `This Event`.

Grid `1fr 52px 132px`, `gap: 8px`. Header row: 10px uppercase letter-spacing `.08em`
`#6b7280`, `padding-bottom: 6px`, bottom border `1px solid #374151`; labels
`Party` / `Dmg` (right-aligned) / `HP after` (right-aligned).

One row per adventurer **this event actually touched**, `padding: 6px 0`, bottom border
`1px solid rgba(55,65,81,.5)`:
- Name 13px `#e5e7eb`; class 10px `#6b7280`; if the row ends at ≤50% HP, the word
  `wounded` in 10px `#ef4444`.
- Damage: 13px `#ef4444`, right-aligned, rendered with a true minus sign: `−4`.
- HP after: 6px-tall bar (`flex: 1`, track `#0b1220`, radius `3px`) + `cur/max` label
  11px. Bar and label share one color: >50% `#4ade80`, >25% `#fbbf24`, else `#ef4444`
  (this is the existing `hpColor()` rule — reuse it, and reuse `ProgressBar.vue`).

Below the table, 11.5px `#6b7280`: `Sister Halan and Maevis Thorn were untouched.`
(join names with `and`; two or more → `A, B and C`; if the event touched everyone, omit
the line entirely.)

Rule: this table shows **only what this event did**. No dealt/spells/cures columns here —
nothing in a trap involves them.

### 3. "Expedition So Far" ledger

Separated by a top border `1px solid #374151`, `padding-top: 14px`.

Label row: `Expedition So Far` (10px uppercase `.12em` `#6b7280`) then, 10px `#6b7280`,
`Days 1–2` (day 1 → current expedition day).

Grid `1fr 106px 78px 78px 78px 78px`, `gap: 6px 8px`, `align-items: center`.
Header cells 10px uppercase `.08em` `#6b7280`, `padding-bottom: 6px`, bottom border
`1px solid #374151`; the four numeric ones right-aligned:

`Adventurer` · `HP` · `Dmg Dealt` · `Dmg Taken` · `Spells Left` · `Cures Left`

One row per party member (all six, dead included), each cell `padding: 5px 0` with
bottom border `1px solid rgba(55,65,81,.5)`:
- Adventurer: name 13px `#e5e7eb` + class 10px `#6b7280`. Dead members keep the existing
  treatment (line-through, 0.6 opacity, `#ef4444`).
- HP: same bar + label as above.
- Dmg Dealt 13px `#4ade80`, Dmg Taken 13px `#ef4444`, Spells Left 13px `#60a5fa`,
  Cures Left 13px `#a78bfa`, all right-aligned. Em dash `—` where a value does not apply
  (a Fighter has no spells; a non-cleric has no cures).
- Spells/Cures are **remaining, not spent**: `2/4` = two of four slots still available.
  This was a deliberate call — the columns are a resource read for the decision the
  player is about to make, not a scorecard.

Totals row (no borders, `padding-top: 7px`): `Expedition total` 11px uppercase `.06em`
`#6b7280`; in the HP column `2 at half or less` (11px `#6b7280`); then party sums in the
matching column colors at 12px, with spells/cures summed as `remaining/total`.

Banked line, 12px `#6b7280`, `gap: 10px`, wraps: `Banked so far` then
`12gp 4sp` (`#fbbf24`) · `210 XP` (`#60a5fa`) · `5 kills` (`#4ade80`). Currency through
the existing `formatCurrency()`. Right-aligned at the end of the same line, the log
toggle: `Expedition Log ▾` / `▴`, underlined, 12px `#6b7280`, hover `#e5e7eb`.

### 4. Expedition Log (nested, collapsed by default)

Container: `1px solid #374151`, radius `6px`, `background #1a1a1a`, `padding: 8px 10px`.

This is the same three-level tree as `ExpeditionSummaryView.vue`'s Expedition Log —
reuse that view's expansion logic (`toggleCombat` / `isCombatExpanded`, `toggleRound` /
`isRoundExpanded`, `roundLabel`, `sideAttacks`, `sideSummary`, `turnUndeadSummary`,
`pluralMonster`, `outcomeClass`). Ideally extract it into a shared
`ExpeditionLog.vue` used by both the summary view and this modal; if that is too much
churn for this change, importing the summary's helpers is acceptable.

Row geometry (all rows share it): `display: flex`, `gap: 8px`, `padding: 3px 4px`,
radius `3px`, hover `rgba(74,222,128,.04)`, caret column fixed `10px` wide, 9px
`#6b7280`; meta pushed right (`margin-left: auto`) at 10.5px `#6b7280`.

- **Turn** — indent 0, 11px / 700 / `#4ade80`, caret `▼`/`▶`, **expanded by default**.
- **Event** — indent 14px, 11.5px `#e5e7eb`. Combat rows are expandable (`▼`/`▶`,
  collapsed by default); non-expandable rows (treasure, trap) show `·` instead of a
  caret. Outcome badge after the label: 9.5px / 700 / `.06em`, `padding: 1px 6px`,
  radius `4px` — Clear Victory green tint, Tough Fight gold tint, defeat red tint.
  Meta: `11 HP lost · +120 XP · 3 killed`. The event that opened this modal appears as
  the last row of the current turn with a gold `This event` badge and its damage meta in
  `#ef4444`.
- **Round** — indent 32px, 11px `#d1d5db`, expandable, collapsed by default. Label from
  `roundLabel()`; meta is the per-side summary
  `Party 2/3 · 7 dmg — Monsters 1/3 · 3 dmg`, or Turn Undead / morale text where those
  apply.
- **Attack line** — indent 50px, 10.5px `#6b7280`, no caret:
  `Kessa Vane → Goblin · roll 14 vs 11 · hit · 5 dmg`, `· slain` appended on a kill,
  spell casts and heals as their own lines (`✚ Sister Halan heals Ilanniel for 3 HP`).

### 5. Decision block

Top border `1px solid #374151`, `padding-top: 14px`. **Three equal columns**
(`grid-template-columns: 1fr 1fr 1fr`, `gap: 10px`), each column a button above its
explanation (`gap: 6px`).

Buttons, 13px / 700, `padding: 9px 12px`, radius `6px`, centred, full column width:
- **Press On** — `background #22c55e`, `color #000`; hover `#4ade80`.
- **Retreat** — `1px solid #4b5563`, `color #d1d5db`; hover border `#4ade80`, text `#e5e7eb`.
- **You Decide** — same as Retreat but hover border `#60a5fa`.

Explanations, 11px / 1.5 / `#6b7280`, always visible (not tooltips):
- Press On → `Continue into the dungeon.`
- Retreat → `Return early.`
- You Decide → `The party decides whether to press on or retreat.`

Set the same three strings as `title` attributes too, so hover/AT get them as well.
Copy rule: say what the button does, never what will happen to the party.

Buttons keep today's behavior exactly: `emit('choose', 'press_on' | 'retreat' | 'auto')`,
disabled while `choosing`. Drop the old `View Full Expedition Details` link — the ledger
now lives in the modal. For `eventType === 'tpk'`, keep today's single
**Rest in Peace** button and hide the decision block.

## Dashboard changes (small, optional but recommended)

1. **Decision badge** on the active-expedition row when `result === 'awaiting_choice'` —
   already implemented in `DashboardView.vue`; no change.
2. **Recently Returned card.** After a retreat the expedition leaves
   `active_expeditions`, and today nothing on the Dashboard says how it ended. Add a card
   (same card styling, 3px `#60a5fa` left accent) with the party name, `Depth n`, a gold
   `Retreated early` badge, the two-line date block below, the brought-home totals, and a
   `View Summary` link.
3. **PLANNED / ACTUAL date block** (fixes the audit bug where a retreat prints the
   planned end date as if it happened). Two labelled lines, label column `62px`, 10px
   letter-spacing `.1em`:
   - `PLANNED` `#6b7280` — `Day 12 → Day 14 · 3 days` (13px `#6b7280`)
   - `ACTUAL` `#4ade80` — `Day 12 → Day 13 · 2 days` (15px `#e5e7eb`)

   Rule: a *completed* expedition shows no PLANNED line at all — the plan is only
   interesting when it was broken. Apply the same block in
   `ExpeditionSummaryView.vue`'s header card, replacing the single
   `start_day — return_day (n days)` paragraph.

## Interactions & behavior

- Trigger unchanged: `SidePanel.advanceDay()` / `skipToEvent()` → `processEvents()` →
  `expedition_choice` queued → `ExpeditionEventModal` opens. Queue behavior, TPK
  auto-resolve, and `next_event` chaining in `popupChoice()` all unchanged.
- On `next_event`, the modal stays open and re-renders with the new message; the
  existing `watch([isOpen, eventMessage])` refetch already covers refreshing the ledger.
- Log expansion state is local to the modal and resets when it closes.
- Transitions: color/border only, 0.1–0.15s. HP/progress bar widths ease 0.3s. No
  entrance animation, no blur, no bounce.
- Loading: keep today's `Loading expedition data...` line while the summary fetch is in
  flight; the event line and the decision block render immediately.
- Failure: if the summary fetch fails, render the event line + decision block alone
  (today's behavior — fail silently, never block the decision).
- Not responsive: desktop only, one width, matching the rest of the app.

## Data availability (read this before estimating)

Everything below comes from the existing `GET` summary payload used by the modal today
(`expeditionsApi.getSummary`) unless marked otherwise.

- Event narrative, subtype → existing `eventMessage` / `eventType` props.
- This-event rows → `events_log`, last turn: `trap_victims[]` (`name`, `damage`) for
  traps; for combat, the round logs' `attacks[]` where the target is a PC. HP after and
  class → `member_results[]`.
- Dmg Taken per adventurer → sum of `damage` over `round_log[].attacks[]` (and
  `halfling_pre_round[]`) where `target` is that PC, across all turns, plus
  `trap_victims[]`. Derivable client-side today.
- Dmg Dealt per adventurer → same sums where `attacker` is that PC. Derivable
  client-side today.
- Kills, loot, XP → `monsters_killed` per combat, `total_loot` / `total_silver` /
  `total_copper`, `total_xp`.
- **Spells Left / Cures Left per adventurer → not currently exposed.** The payload only
  has party-level `spells_left` and `heals_left`. This is the one backend addition the
  design wants: per-member `spells_left` / `spells_max` / `cures_left` / `cures_max` on
  `member_results`. If that is out of scope for this pass, ship the columns showing
  `—` for every member and put the party-level `spells_left` / `heals_left` in the
  totals row; the layout does not change when the per-member data lands.

## State

All local to `ExpeditionEventModal.vue`; nothing new in Pinia.

- `summary` / `loading` — existing.
- `logOpen: boolean` — the Expedition Log disclosure, default false.
- `expandedCombats: Set<string>` / `expandedRounds: Set<string>` — keyed
  `${turn}-${eventIdx}` and `${turn}-${eventIdx}-${roundIdx}`, same scheme as
  `ExpeditionSummaryView.vue`. Default empty.

## Design tokens

All already declared in `frontend/src/assets/main.css`; use the variables, not the hexes.

Surfaces `#000` app · `#1a1a1a` log panel · `#1f2937` card/input · `#111827` modal ·
`#0b1220` bar track.
Green `#4ade80` / `#22c55e` / `#166534`. Status: gold `#fbbf24`, blue `#60a5fa`,
red `#ef4444`, purple `#a78bfa`. Tints at 15% (badges), washes at 8% / 4% (hover).
Text `#e5e7eb` / `#d1d5db` / `#6b7280`, on-green `#000`.
Lines `#4b5563` default, `#374151` rules, `rgba(55,65,81,.5)` table row rules.
Type: mono only — `'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas',
'Monaco', 'Courier New', monospace`. Sizes used here: 9/9.5/10/10.5/11/11.5/12/13/15px.
Spacing 4 / 6 / 8 / 10 / 12 / 14 / 16px. Radii 6px containers, 4px badges, 3px bars.
Shadows: card `0 2px 8px rgba(0,0,0,.5)`, modal `0 0 40px rgba(0,0,0,.8)`.

## Assets

None. All glyphs are unicode: `▶` `▼` `▴` `▾` `×` `·` `—` `−` `→` `✚` `☰`.
No icon library, no images.

## Files in this bundle

- `VentureKeep P2 - Dashboard to Event.dc.html` — the design (authoritative).
- `VentureKeep P1 - Expedition Event + Summary.dc.html` — the exploration that led here.
- `_ds/` — the design-system tokens and stylesheets the prototypes link to; the app's own
  `main.css` already carries the same values.
- `support.js` — runtime for the prototype files. Not part of the app.

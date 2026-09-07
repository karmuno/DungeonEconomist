# Handoff: The Economic Loop (Upkeep Day + Treasury Forecast + Village)

## Overview

Three changes that make one chain readable on screen, with no documentation:

> expeditions → adventurers earn → monthly upkeep flows to the treasury → treasury buys
> buildings → assigned adventurers activate bonuses → stronger expeditions

1. **Upkeep Day** becomes a modal event on the day it happens — the treasury delta and
   the Collect button first, then the per-adventurer ledger that explains it. Nothing in
   the app's state moves until Collect is pressed.
2. **A persistent upkeep forecast** in the sidebar under Treasury — one line, clickable
   into a read-only Upkeep Forecast modal with the full per-adventurer table, plus a red
   list of adventurers who will not be able to pay.
3. **The Village screen** is rebuilt around numbers: current effect values, the exact
   effect of the next tier, slots with level requirements, who is assigned, and a
   click-to-assign popover on every empty slot.

Plus one cross-cutting addition: **every adventurer name anywhere in these screens opens
that adventurer's character sheet.**

## About the design files

The three `.dc.html` files in this bundle are **design references written as standalone
HTML prototypes** — self-contained mocks with fake data and their own tiny state
machines. They are not production code and should not be copied into the app. Recreate
them in the existing Vue 3 + TypeScript frontend using that codebase's established
patterns (`<script setup>`, Pinia stores, `ModalDialog.vue`, `ProgressBar.vue`, the CSS
custom properties in `frontend/src/assets/main.css`).

| File | Screen |
| --- | --- |
| `Q1a - Upkeep Modal.dc.html` | Upkeep Day modal, day 30. Click **Collect**; then click either sidebar notification to reopen it as a receipt. |
| `Q7c - At risk- treasury line.dc.html` | Dashboard at day 24 — sidebar forecast line + at-risk list. Click `+229gp 7sp` (or the red list) for the Upkeep Forecast modal. |
| `Q6a - Assign- inline popover.dc.html` | Village. Click the dashed **Empty · Fighter Lv 3+** slot on Training Grounds. |

Adventurer names are underlined in all three — click any of them.

## Fidelity

**High fidelity.** Colors, type sizes, spacing, borders and radii are final and are all
existing tokens from the app's own CSS. Recreate the modals and the Village cards
pixel-for-pixel. The surrounding Dashboard chrome (header, sidebar, roster card, active
expeditions) is a stand-in for the real views — do **not** rebuild it from these files;
only the sidebar changes listed under *Sidebar changes* are in scope there.

## Files to change

| File | Change |
| --- | --- |
| `frontend/src/components/layout/SidePanel.vue` | Treasury block gains the forecast line + at-risk list; both open the forecast modal. Upkeep notifications become clickable. |
| `frontend/src/components/upkeep/UpkeepDayModal.vue` | **New.** The Upkeep Day event modal. |
| `frontend/src/components/upkeep/UpkeepForecastModal.vue` | **New.** The read-only forecast. Shares the table markup with the above. |
| `frontend/src/views/VillageView.vue` | Rewrite the building card template + styles. All the Village work. |
| `frontend/src/components/village/AssignPopover.vue` | **New.** The eligible-adventurer popover for an empty slot. |
| `frontend/src/components/adventurers/AdventurerDetail.vue` | Reused as-is inside `ModalDialog`; add the **Upkeep** row (see *Character sheet*). |
| `frontend/src/stores/gameTime.ts` | Route the `upkeep` day event into the new modal instead of a notification only. |

No changes to the router, `api/expeditions.ts`, `DashboardView.vue`, or the roster rows
(a deliberate call — the roster does **not** show upkeep; the sidebar and the two modals
own that story).

---

## Screen 1: Upkeep Day modal

**Trigger.** Day advance produces the existing `upkeep` event (every 30 days). The modal
opens *before* the treasury value changes anywhere in the UI — the player sees the event
that causes the state change, then causes it themselves with **Collect**. This is the
binding sequencing rule; do not update `player.treasury*`, adventurer purses, or the
bankruptcy state until the Collect request resolves.

**Container.** Existing `ModalDialog.vue`, scrim `rgba(0,0,0,.75)`, dialog
`background: var(--bg-modal)` (`#111827`), `1px solid #4b5563`, radius `6px`,
`box-shadow: 0 0 40px rgba(0,0,0,.8)`, **width 760px**, `max-height: 88vh`,
`overflow-y: auto`. Body padding `16px`, section gap `16px`.

**Header** — `padding: 12px 16px`, bottom border `1px solid #374151`:
`Upkeep Day` 15px/700 `#4ade80`, then 11px `#6b7280`: `Day 30 · 8 adventurers · 1cp per XP`.
Right: `×` 15px `#6b7280` — behaves exactly as Collect (there is no way to defer the day).

### 1. Outcome row (first, above the ledger)

One row, `gap: 12px`, `padding-bottom: 14px`, bottom border `1px solid #374151`:

- `TREASURY` 10px uppercase `.12em` `#6b7280`
- `412gp` 15px `#6b7280` · `→` 15px `#6b7280` · **`573gp 4sp`** 20px/700 `#4ade80`
- `2 to debtor's prison` 11px `#ef4444`
- `39gp 5sp deferred` 11px `#60a5fa`
- **Collect** — `margin-left: auto`, `padding: 9px 24px`, `background #22c55e`,
  `color #000`, radius `6px`, 13px/700. Label becomes **Close** when the modal is
  reopened from a notification.

Rule: the answer comes first. The tables below are the evidence, not the lede. There is
no narrative sentence — the badge and the numbers carry it.

### 2. "At the Keep" ledger

Section label 10px uppercase `.12em` `#6b7280`.
Grid `1fr 84px 84px 84px 96px`, `gap: 0 8px`. Header cells 10px uppercase `.08em`
`#6b7280`, `padding-bottom: 6px`, bottom border `1px solid #374151`:
`Adventurer` · `XP` · `Upkeep` · `Purse` · `After` (last four right-aligned).

One row per adventurer at the keep, cells `padding: 6px 0`, bottom border
`1px solid rgba(55,65,81,.5)`:

- Name 13px `#e5e7eb` (clickable — see *Character sheet*), class + level 10px `#6b7280`.
- XP 12px `#60a5fa`. Upkeep 13px `#4ade80`. Purse 12px `#6b7280`. After 12px `#fbbf24`.
- **Cannot pay:** name, upkeep, purse and after all `#ef4444`, after shows the negative
  (`−15gp`), and a `DEBTOR'S PRISON` badge follows the class: 9.5px/700 `.06em`,
  `padding: 1px 6px`, radius `4px`, `#ef4444` on `rgba(239,68,68,.15)`.

Totals row (`padding-top: 7px`, no borders): `COLLECTED` 11px uppercase `.06em`
`#6b7280`, the summed XP **of the payers only** 12px `#60a5fa`, the gold 13px/700
`#4ade80`, then `28gp 8sp unpaid` 11px `#ef4444` spanning the last two columns.

### 3. "On Expedition" — deferred

Label `On Expedition` + 10px `#6b7280` `collected on return`.
Grid `1fr 84px 84px 180px`: name/class, XP, deferred amount (13px `#60a5fa`), and
`The Demo Divers · due day 31` 11px `#6b7280`. Totals row `DEFERRED` + summed XP + total.

Rule: deferred upkeep is never silently missing — it is a labelled section with its own
total, so the treasury delta and the monthly total can differ without surprising anyone.

### 4. After Collect

The modal closes. Sidebar notifications (existing `notif` styles) record it:

- warning: `Maevis Thorn and Rowan Ashe could not pay their upkeep and were sent to debtor's prison.`
- success: `Upkeep collected: 161gp 4sp from 4 adventurers.`

Both notifications are **clickable** and reopen the modal read-only (Collect → `Close`),
with an underlined `Upkeep` action label at the right of the notification, matching the
existing `notif-action` pattern.

---

## Screen 2: sidebar forecast + Upkeep Forecast modal

### Sidebar changes (`SidePanel.vue`)

Under the existing treasury value, a clickable line, `margin-top: 2px`, `gap: 6px`:

- `+229gp 7sp` 11px `#4ade80`, underlined
- `upkeep · day 30` 10px `#6b7280`

Below it, when any adventurer's purse is short of their upkeep, a red block
(also clickable, `margin-top: 4px`, `gap: 1px`):

```
2 adventurers cannot afford upkeep:
  Maevis Thorn
  Rowan Ashe
```

Heading and names 10px `#ef4444`; names indented `padding-left: 8px`. Singular form
`1 adventurer cannot afford upkeep:` when there is one. Names are clickable to the
character sheet (stop propagation so they don't also open the forecast).

### Upkeep Forecast modal

Same shell, **width 640px**. Header: `Upkeep Forecast` + `Day 30 · in 6 days`.

**Top row** (`padding-bottom: 14px`, bottom border `1px solid #374151`), three figures
separated by literal `+` and `=` glyphs (18px `#6b7280`):

| | label (10px uppercase `.1em` `#6b7280`) | value |
| --- | --- | --- |
| | `Treasury now` | `412gp` 20px/700 `#e5e7eb` |
| `+` | `Collecting` | `229gp 7sp` 20px/700 `#4ade80` |
| `=` | `Treasury day 30` | `641gp 7sp` 26px/700 `#4ade80` |

**One total, no splits.** The forecast does *not* break out deferred vs. collected —
that distinction belongs to the day itself, in the Upkeep Day modal. Deliberate call
from review: the forecast answers "how much, and when", nothing else.

**Table.** Grid `176px 76px 40px 90px 56px 80px 72px`, **no column gaps** — horizontal
padding lives inside the cells (`padding: 5px 8px 5px 0` left-aligned,
`padding: 5px 0 5px 8px` right-aligned) so every row rule runs unbroken from the first
column to the last. Every cell is `display:flex; align-items:center` (do **not** put
`align-items:center` on the grid — that shrink-wraps cells and staggers the rules).

Columns: `Adventurer` · class · level · flag · `XP` · `Upkeep` · `Purse`. **Class and
level have no headers** — they read as continuations of the name, 10px `#6b7280`.
Flag column holds `SHORT 15gp` (9.5px/700 `#ef4444` on `rgba(239,68,68,.15)`) for anyone
whose purse won't cover the bill; their name, upkeep and purse also go `#ef4444`.
Totals row: `8 adventurers` · `22,970` · `229gp 7sp`.

All adventurers appear in one list — no separate section for expedition members here.

---

## Screen 3: Village

Grid `repeat(2, 1fr)`, `gap: 12px`, one card per building. Card: `#1f2937`,
`1px solid #4b5563`, radius `6px`, shadow `0 2px 8px rgba(0,0,0,.5)`, padding `12px 16px`,
`display:flex; flex-direction:column; gap:8px`, 3px left accent — `#4ade80` built,
`#6b7280` + `border-style: dashed` + `opacity:.85` unbuilt.

**Header:** name 14px/700 `#4ade80`, then `LEVEL 2` (green badge) or `NOT BUILT` (grey
badge), then the class 10px `#6b7280` right-aligned.

**Current effects** — `min-height: 96px` (this is what keeps the upgrade block level
across a row). One row per stat, `padding: 3px 0`, bottom border
`1px solid rgba(55,65,81,.5)`: label 10px uppercase `.06em` `#6b7280` on the left, value
12px `#e5e7eb` on the right, `—` `#6b7280` where the tier does not grant it.
Every value is the **number from config**, not a description: `+1 HP/day per Cleric`,
`+1 per Fighter`, `2 · Fighter Lv 3+`, `−1 party morale`.

**Assigned** — `min-height: 26px`, label + chips. Chip: `padding: 3px 6px`,
`background rgba(74,222,128,.08)`, `1px solid rgba(74,222,128,.15)`, radius `3px`;
name 11px `#e5e7eb` (clickable), level 10px `#6b7280`, `×` 11px `#6b7280`.
Empty slot: same box with `1px dashed #4b5563`, 10px `#6b7280`,
`Empty · Fighter Lv 3+` — hover turns border and text `#4ade80`.

**Next tier** — top border `1px solid #374151`, `padding-top: 8px`. Label
`UPGRADE TO WAR COLLEGE` / `WHEN BUILT` 10px uppercase `.06em` `#6b7280`. Then the same
stat labels with the next tier's values: **`#4ade80` where the value changes, `#6b7280`
where it does not.** That colour difference is the entire "what does this buy me"
explanation — no sentence.

**Button** — `margin-top: auto` so it pins to the card bottom and aligns across the row.
Affordable: `#22c55e` on `#000`. Unaffordable: `#1a1a1a`, `1px solid #4b5563`, `#6b7280`.
Label `Build · 50gp` / `Upgrade · 1,250gp`.

**Affordability:** cost only. No "time to afford", no treasury progress bar — reviewed
and cut. An unaffordable price simply reads as unaffordable.

### Assign popover

Clicking an empty slot opens a popover: `position:absolute; top:26px; left:0; width:100%`
(anchor is the assigned row, which needs `position:relative`), `z-index:5`, `#111827`,
`1px solid #4b5563`, radius `6px`, shadow `0 2px 8px rgba(0,0,0,.5)`, padding `6px`.

Popover header (`padding: 2px 8px 6px`, bottom border `1px solid #374151`):
`FIGHTER · LV 3+` 10px uppercase `#6b7280`, then the bonus the assignment activates —
`+1 to-hit · +1 dmg` 10px `#4ade80` — then `×`.

Rows, grid `112px 40px 52px 64px 60px 1fr`, `padding: 5px 8px`, radius `3px`, hover
`rgba(74,222,128,.06)`: name 12px `#e5e7eb` · level 10px `#6b7280` · HP 10px `#4ade80` ·
`2,900 XP` 10px `#60a5fa` · purse 10px `#fbbf24` · current posting 10px `#6b7280`
(`Unassigned` or the party name).

**Only eligible adventurers appear** — right class, at or above the tier's minimum level,
alive, not bankrupt. Ineligible adventurers are not listed at all (reviewed: showing them
greyed out was noise). Picking one fills the slot with a chip; `×` on the chip unassigns.

---

## Character sheet (all three screens)

Every adventurer name is a clickable span: `cursor:pointer`, `text-decoration:underline`,
`text-decoration-color:#374151`, `text-underline-offset:2px`. Click opens the existing
`AdventurerDetail.vue` in a `ModalDialog` at **width 420px**, `z-index` above any modal
already open (the prototypes use `z-index: 20` on the scrim).

Rows, `padding: 6px 0`, bottom border `1px solid rgba(55,65,81,.5)`; label column `78px`,
10px uppercase `.08em` `#6b7280`; value right-aligned 13px:

- `HP` — bar + `17/20` `#4ade80`
- `XP` — bar + `3,200 / 8,000` `#60a5fa`
- `Purse` — `38gp` `#fbbf24`
- `Upkeep` — `32gp` `#4ade80` ← **the one new row**; the adventurer's own monthly
  contribution, so the causal link (more XP ⇒ more income) is legible from the sheet
  rather than from the roster.
- `Items` — `Longsword +1` `#fbbf24`, `—` when none
- `Status` — 12px `#6b7280`, e.g. `Assigned · Training Grounds`,
  `On expedition · The Demo Divers`, `At the keep · 15gp short of upkeep`

Deliberate call: **the roster rows do not show upkeep.** The sidebar, the two upkeep
modals and this sheet own it.

## Interactions & behavior

- Transitions: colour/border only, 0.1–0.15s. Bar widths ease 0.3s. No entrance
  animation, no blur, no bounce.
- The forecast modal is read-only; the only actions are `×` and `Close`.
- Popover state is local to the Village card and closes on `×` or on picking.
- The character sheet closes back to whatever was underneath it.
- Not responsive: desktop only, one width, matching the rest of the app.

## Data availability

Everything is computable from data the app already has:

- **Per-adventurer upkeep** = `adventurer.xp` cp, i.e. `xp / 100` gp. Monthly total =
  sum over the roster. Both are pure functions of current XP — no new endpoint.
- **Next upkeep day** = next multiple of 30 after `gameTime.currentDay`.
- **Cannot pay** = `purse_in_cp < xp`. Shortfall = the difference. Available before the
  day, which is what makes the sidebar warning possible.
- **Deferred** = adventurers with `on_expedition`; their upkeep is collected on return
  (existing behavior) — the modal only needs to *label* them and total them separately.
- **Buildings**: `buy_cost`, `upgrade_cost`, `max_assigned`, `min_adventurer_level`,
  `assigned_adventurers`, `effects[]` all exist on `BuildingData` today.
- **Next-tier values** are the one gap: `BuildingData` exposes `assigned_bonus_desc` and
  `effects[]` for the *current* level only. The Village card needs the **next tier's
  numbers** to render the green/grey delta column. Add `next_effects: string[]` (same
  shape as `effects`) and `next_max_assigned` / `next_min_adventurer_level` to the
  buildings payload. Until that lands the card can render the next-tier column from the
  static tier config on the client; the layout does not change when the API catches up.

## State

- `UpkeepDayModal`: `collected: boolean`, `reopened: boolean`. Nothing new in Pinia
  beyond routing the `upkeep` event to the modal.
- `UpkeepForecastModal`: `open: boolean` on `SidePanel`.
- `VillageView`: `pickingSlot: {buildingId, slotIndex} | null`.
- Character sheet: `sheetAdventurerId: number | null`, hoisted wherever names render.

## Design tokens

All already declared in `frontend/src/assets/main.css`; use the variables, not the hexes.

Surfaces `#000` app · `#1a1a1a` panel · `#1f2937` card · `#111827` modal · `#0b1220` bar
track. Green `#4ade80` / `#22c55e` / `#166534`. Status: gold `#fbbf24`, blue `#60a5fa`,
red `#ef4444`, purple `#a78bfa`. Tints at 15% (badges), washes at 8% / 6% / 4% (hover).
Text `#e5e7eb` / `#d1d5db` / `#6b7280`, on-green `#000`. Lines `#4b5563` default,
`#374151` rules, `rgba(55,65,81,.5)` table row rules.
Type: mono only — `'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', 'Monaco',
'Courier New', monospace`. Sizes: 9.5/10/11/12/13/15/18/20/24/26/32px.
Spacing 2 / 4 / 6 / 8 / 10 / 12 / 14 / 16 / 24px. Radii 6px containers, 4px badges,
3px bars and chips. Shadows: card `0 2px 8px rgba(0,0,0,.5)`, modal
`0 0 40px rgba(0,0,0,.8)`.

**Number formatting:** thousands separators above 999 everywhere (`8,200 XP`,
`22,970`, `1,250gp`). Currency through the existing `formatCurrency()`
(`161gp 4sp`, `6gp 4sp`, `0cp`). Negative values use a true minus sign (`−15gp`).

## Assets

None. All glyphs are unicode: `×` `·` `—` `−` `→` `▶` `▼` `☰` `+` `=`.
No icon library, no images. Magic items are rendered as words (`Longsword +1`) — the
emoji item markers used elsewhere in the app do not render in the mono stack at 13px.

## Reused vs. new

**Reused unchanged:** `ModalDialog.vue`, `ProgressBar.vue`, notification styles and the
`notif-action` pattern, badge/chip/card/button styles, `formatCurrency()`,
`AdventurerDetail.vue` (one row added).

**New:** `UpkeepDayModal.vue`, `UpkeepForecastModal.vue`, `AssignPopover.vue`, the
sidebar forecast + at-risk block, the rebuilt Village card.

## Out of scope

No new simulation systems, no history view, no recruitment/class-XP bonus redesign, no
auto-delve explanation. Event-before-state sequencing, the "brought back X" sidebar copy
and the dead/empty party lifecycle are being handled directly in code.

## Files in this bundle

- `Q1a - Upkeep Modal.dc.html` — Upkeep Day (authoritative).
- `Q7c - At risk- treasury line.dc.html` — Dashboard sidebar forecast + forecast modal.
- `Q6a - Assign- inline popover.dc.html` — Village + assign popover.
- `_ds/` — design-system tokens and stylesheets the prototypes link to; the app's own
  `main.css` already carries the same values.
- `support.js` — runtime for the prototype files. Not part of the app.

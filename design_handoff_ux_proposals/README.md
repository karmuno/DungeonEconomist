# Handoff: VentureKeep UX Proposals (three mocks)

## Overview

This bundle contains three proposed UX improvements for **VentureKeep** (a browser-based RPG barony management sim by Stahl Systems, repo [karmuno/DungeonEconomist](https://github.com/karmuno/DungeonEconomist)). The mocks were produced in HTML/React for design review. This package gives a developer everything needed to implement them in the production codebase.

The three improvements, in priority order:

1. **Day Report modal** *(top recommendation)* — a per-day narrative summary that appears when the player clicks "Advance Day". Groups events by expedition / keep, reveals entries one at a time with a short animation, and ends with a treasury delta + "Advance" confirm.
2. **Keep Select · delete-confirm popover** *(quick win)* — replaces the current row-collapse confirmation (which shifts layout) with an anchored popover next to the Delete button.
3. **Normalized currency with hover detail** *(quick win)* — replaces `127gp 3sp 5cp` style strings with a single normalized gp value (`127.4gp`); hovering reveals the exact denomination breakdown.

## About the design files

The files in `mocks/` are **design references created in HTML + React-via-Babel-standalone** — prototypes showing intended look and behavior, not production code to copy directly. The task is to **recreate these designs in the VentureKeep codebase's existing environment** (Vue 3 + TypeScript + Vite) using its established patterns, stores, and component conventions.

Open `preview/index.html` in a browser to see all three mocks rendered live in iframes with their source filenames labelled.

## Fidelity

**High-fidelity.** Colors, spacing, typography, and component behavior are intentional and match the existing VentureKeep visual system (`reference/colors_and_type.css`). Recreate pixel-accurately using the codebase's existing Vue components and global CSS tokens where they exist; add new components where they don't. Treat the mocks as **spec**, not as direction — the user wants these shipped substantially as shown.

## Target codebase context

- **Frontend:** Vue 3 + TypeScript + Vite. **Not React.** Do not port the JSX literally; re-author as idiomatic Vue 3 SFCs (`<script setup lang="ts">`) and reuse existing components where the repo already has equivalents (buttons, cards, modals).
- **Backend:** FastAPI + SQLAlchemy + SQLite/Postgres. Only the Day Report mock (#1) has any backend implication — see its section below.
- **Design language:** retro-terminal, JetBrains Mono everywhere, black background, green (`#4ade80`) as primary accent, gold (`#fbbf24`) for money, blue (`#60a5fa`) for XP/choice, red (`#ef4444`) for danger/combat. No gradients, no textures, no rounded-corner-plus-left-border-accent containers, no emoji.

## Files in this bundle

```
design_handoff_ux_proposals/
├── README.md                       ← this file
├── mocks/
│   ├── index.html                  ← runs all three mocks on a design canvas (pan/zoom grid)
│   ├── vk_styles.js                ← shared inline style tokens (the visual spec)
│   ├── design-canvas.jsx           ← canvas scaffolding (not part of the deliverable, ignore)
│   ├── mock1_keep_select.jsx       ← Keep Select delete-confirm popover
│   ├── mock2_currency.jsx          ← Normalized currency + hover tooltip
│   └── mock3_day_report.jsx        ← Day Report modal
├── preview/
│   ├── index.html                  ← open this — shows each mock in its own iframe, labelled
│   └── _single.html                ← iframe host (internal)
└── reference/
    └── colors_and_type.css         ← production color + type tokens from the VentureKeep design system
```

The **authoritative visual spec** is `mocks/vk_styles.js` (tokens) + each mock's JSX (structure and behavior). The `preview/index.html` is the fastest way to see what to build.

---

# Spec 1 · Day Report modal *(top recommendation)*

**Source:** `mocks/mock3_day_report.jsx`

## Purpose

When the player clicks "Advance Day", the game currently advances silently — notifications fan out across a sidebar feed, and the player has to reconstruct what happened. The Day Report converts that silent clock-tick into a single consequential beat: a modal that animates in, reveals the day's events in order (grouped by expedition / keep), shows the treasury delta, and has the player explicitly confirm "Advance Day".

This is the app's new signature interaction. It replaces the global notification feed — all per-day event reporting moves here.

## When it opens

- Player clicks "Advance Day" (the primary CTA). The action does not advance immediately; it opens the report in a staged state.
- Player clicks "Skip to Event". The report opens, shows silent days' summary lines, then pauses at the next consequential event.

## Layout

Full-viewport backdrop: `rgba(0, 0, 0, 0.75)`, centered modal.

Modal card:
- `max-width: 560px`, `max-height: 90vh`, scrollable if overflowed
- Background: `var(--bg-card)` = `#1f2937`
- Border: `1px solid var(--border-color)` = `#4b5563`
- Border-radius: `var(--radius)` = `6px`
- Box-shadow: `0 2px 8px rgba(0,0,0,.5)`
- Entry animation: `opacity 0 → 1`, `translateY(8px → 0)`, 300ms ease-out

### Header (`padding: 12px 16px`, bottom-bordered)
- Left:
  - Eyebrow: `DAY REPORT` — 10px, uppercase, `letter-spacing: .1em`, color `var(--text-muted)` = `#6b7280`
  - Title row: `<h2>Day {n}</h2>` (1.4rem, `var(--accent-green)`) + inline `{calendar}` (11px, muted) — e.g. `Day 43  Hearthmoon 12`
- Right: `⟲ Replay` button (`btn btn-secondary btn-sm`) — resets the reveal animation

### Body (`padding: 16px`)

Two (or more) sections, each representing a scope:

**Section header** (12px bottom-margin, 4px bottom-padding, border-bottom):
- `<h3>` in **blue** (`var(--accent-blue)` = `#60a5fa`) for expedition sections
- `<h3>` in **green** (`var(--accent-green)` = `#4ade80`) for keep sections
- Optional `· {subtitle}` inline in muted 11px — e.g. "· The Silent Seven"

**Section entries** (each `padding: 6px 0`, bottom-bordered `1px solid var(--border-subtle)` = `#374151`):
- 6×6px colored dot, top-aligned (`margin-top: 6px`), color by entry type:
  - `info` → muted `#6b7280`
  - `combat` → red `#ef4444`
  - `loot` → gold `#fbbf24`
  - `choice` → blue `#60a5fa`
  - `healing` → green `#4ade80`
  - `upkeep` → gold `#fbbf24`
  - `tavern` → green `#4ade80`
- Text: 12px `var(--text-primary)` = `#f3f4f6`
- Optional detail line: 11px muted; if the entry has `choice: true`, detail is italicized and colored blue
- Entries reveal one at a time, 250ms apart, via `opacity` + `translateY(4px → 0)` transition (300ms)

### Day-summary footer

Only appears after all entries have revealed. Animates in with the same `dayIn` keyframe.

Container: `padding: 10px`, `background: var(--bg-secondary)` = `#0f1419`, 1px border, `var(--radius)` rounding. Flex row, `space-between`.

- Left:
  - Eyebrow: `TREASURY` (10px, uppercase, muted)
  - Value row: `{before}` (muted, strikethrough-adjacent) → arrow `→` (muted, 6px margin) → `{after}` (gold, bold) → `{delta}` (green, 11px, 8px left-margin)
  - e.g. `127.4gp  →  145.1gp  +17.6gp`
- Right (button row, 6px gap):
  - `Dismiss` (`btn btn-secondary btn-sm`) — closes without advancing (lets the player open the Village/Tavern before committing the day)
  - `Advance Day ▸` (`btn btn-primary btn-sm`) — commits the day, closes the modal

### Mid-animation control

While entries are still revealing, a centered `Skip animation` button appears below the last entry (`btn btn-secondary btn-sm`, `margin-top: 10px`) — clicking it completes the reveal instantly.

## Data shape (what the backend needs to send)

The modal needs a structured day-report payload. Suggested shape (mirrors the mock):

```ts
interface DayReport {
  day: number;                       // 43
  calendar: string;                  // "Hearthmoon 12"
  treasuryBefore: { g: number; s: number; c: number };
  treasuryAfter:  { g: number; s: number; c: number };
  sections: DayReportSection[];
}

interface DayReportSection {
  title: string;                     // "Crypt of the Mad King · Depth 2" or "Keep"
  subtitle?: string;                 // "The Silent Seven"
  kind: 'expedition' | 'keep';       // controls header color
  entries: DayReportEntry[];
}

interface DayReportEntry {
  t: 'info' | 'combat' | 'loot' | 'choice' | 'healing' | 'upkeep' | 'tavern';
  text: string;                      // "Encountered 3 skeletons."
  detail?: string;                   // "Sister Vale turns 2 undead. Pip lands the killing blow..."
  choice?: boolean;                  // italicizes & blues the detail line
}
```

**Backend change (FastAPI):** the "Advance Day" endpoint currently returns an end-state. It should additionally return a `DayReport` describing what happened during that tick — or add a sibling endpoint `POST /api/keeps/{id}/advance-day/report` that runs the tick, caches the resolution, returns the report, and commits on a follow-up `confirm` call.

Because the modal has a "Dismiss" button that is expected to let the player navigate the keep before committing, **the day advance must be committed only when the player clicks "Advance Day ▸"**. If the player navigates away with Dismiss and then clicks advance-day again, the same resolved report should re-open. This implies the resolution is stored in a transient "pending-advance" slot on the keep.

If refactoring the backend is out of scope for the first pass, ship the modal as a purely client-side aggregator of existing notification events (still a big UX improvement) and capture the backend change as a follow-up. The modal's structure is designed to work either way.

## Interactions

- `Escape` or backdrop click does **not** dismiss (explicit action required — the player must choose Dismiss or Advance).
- `Replay` button: resets `revealedCount` to 0 and re-runs the interval.
- `Skip animation`: sets `revealedCount = total` immediately.
- After all entries revealed, the footer fades in with `dayIn` (300ms).

## State & persistence

- The report is ephemeral — it's reconstructed from the tick's resolution each time.
- A "pending day advance" needs to persist on the keep if the user dismisses and comes back later (handled server-side; see Backend change above).

---

# Spec 2 · Keep Select — delete-confirm popover *(quick win)*

**Source:** `mocks/mock1_keep_select.jsx`

## Purpose

The current delete confirmation expands the keep row inline, shifting all surrounding rows. This is jarring and obscures context. Replace with an anchored popover that floats over the layout.

## Layout

### Keep row (unchanged baseline structure)
- Flex row, `space-between`, `padding: 12px 16px`
- Background `var(--bg-secondary)` = `#0f1419`, border `1px solid var(--border-color)` = `#4b5563`, `var(--radius)` rounding
- Left column:
  - Row 1 (baseline-aligned, flex-wrap): `<strong>{keep.name}</strong>` + muted italic `vs.` + green-bold `{dungeon.name}` (13px, 700)
  - Row 2: muted 12px — `Day {n} · {gold}gp[ · {buildings}]`
- Right: `Delete` button, small, transparent, 1px muted border

### Popover (new)

Positioned absolutely inside the `Your Keeps` card, anchored so its arrow tip aligns with the horizontal center of the clicked Delete button, and top is 8px below the button.

Computed with `getBoundingClientRect()`:
```js
const r = deleteButton.getBoundingClientRect();
const host = keepsCard.getBoundingClientRect();
const top = r.bottom - host.top + 8;
const buttonCenterFromRight = host.right - (r.left + r.width / 2);
// Popover width = 260px; arrow is 120px from its right edge so it sits at button center.
const right = Math.max(0, buttonCenterFromRight - 120);
```

Popover box:
- `width: 260px`, `padding: 12px`
- Background `#111827`, border `1px solid var(--accent-red)` = `#ef4444`, `var(--radius)` rounding
- Box-shadow `0 8px 24px rgba(0,0,0,.7)`
- Z-index `11`; a transparent full-viewport `fixed` overlay at z-index `10` closes the popover on outside click

Popover content:
- Title row (12px, 600): `Delete <span color=red>{keep.name}</span>?`
- Body (11px muted): `This is permanent. All adventurers, parties, and progress in <strong>{keep.name}</strong> will be lost.`
  - The `<strong>` uses `var(--text-secondary)` = `#9ca3af`, NOT red — only the title echoes the name in red.
- Button row (flex end, 6px gap):
  - `Cancel` (`btn btn-secondary btn-sm`) — closes popover
  - `Delete Forever` (`btn btn-danger btn-sm`) — fires the delete

Arrow (decorative caret):
- 10×10px square, `top: -6px`, positioned so its center aligns with the button center:
  - With the popover's right edge at `buttonCenterFromRight - 120` from host's right, the arrow sits at `right: 120 - 5 = 115px` from the popover's right edge
- Rotated 45°, same red border on top + left only, background `#111827`

## Interactions

- Clicking `Delete` on a row opens the popover anchored to that row's button.
- Clicking `Cancel`, clicking outside the popover, or pressing `Escape` (nice-to-have) closes it without action.
- Clicking `Delete Forever` fires the actual DELETE to the backend; on success, the row is removed from the list.
- Only one popover open at a time.

## State

```ts
const confirmId = ref<number | null>(null);
const anchorRect = ref<{ top: number; buttonCenterFromRight: number } | null>(null);
```

Clearing `confirmId` closes the popover.

---

# Spec 3 · Normalized currency with hover detail *(quick win)*

**Source:** `mocks/mock2_currency.jsx`

## Purpose

`127gp 3sp 5cp`-style strings wrap awkwardly in narrow columns, are hard to scan, and visually over-report low-denomination noise. Show a single normalized gp value with one decimal of precision; reveal the full breakdown on hover.

## Normalization rules

OSR convention: **1gp = 10sp = 100cp**.

```ts
function normalizeGp(g: number, s: number, c: number): string {
  const totalCp = g * 100 + s * 10 + c;
  const gpFloat = totalCp / 100;
  if (gpFloat >= 10) return gpFloat.toFixed(0);  // "145"
  if (gpFloat >= 1)  return gpFloat.toFixed(1);  // "4.7"
  return gpFloat.toFixed(2);                      // "0.83"
}
```

Then append `gp` literal.

**Worked examples** (from the mock's sample data):
| g  | s | c | displayed |
|----|---|---|-----------|
| 47 | 3 | 0 | 47gp      |
| 22 | 0 | 4 | 22gp      |
| 130| 0 | 5 | 130gp     |
| 0  | 8 | 3 | 0.83gp    |
| 19 | 5 | 0 | 20gp      |
| 0  | 0 | 9 | 0.09gp    |
| 127| 3 | 5 | 127gp     |

## Presentation

The `<Purse>` component wraps a span:
- Color: `var(--accent-gold)` = `#fbbf24`
- `border-bottom: 1px dotted var(--accent-gold)` — signals interactivity
- `cursor: help`

## Tooltip (on hover/focus)

- Positioned absolute, `bottom: calc(100% + 6px)` from the trigger, `right: 0` (right-aligned under the value)
- Background `#0a0a0a`, border `1px solid var(--accent-gold)`, `border-radius: 4px`, `padding: 6px 10px`
- `font-size: 11px`, `white-space: nowrap`
- Box-shadow `0 4px 12px rgba(0,0,0,.6)`
- Content:
  - Eyebrow: `PURSE` — 9px, uppercase, muted, `letter-spacing: .08em`, `margin-bottom: 3px`
  - Value: gold `{g}gp` + muted `·` + gold `{s}sp` + muted `·` + gold `{c}cp`
- Arrow: 8×8px rotated-45° caret at `bottom: -5px`, `right: 12px`, gold border on right + bottom only

Show on `mouseenter` / `focusin`, hide on `mouseleave` / `focusout`.

## Where it applies (audit)

Every place the UI currently renders a multi-denomination string should become `<Purse>`:
- Treasury readout on the Keep dashboard sidebar
- Per-adventurer purse column in Tavern and Party rosters
- Keep Select meta line (`Day 42 · 127gp · Temple, Smithy` — swap the `127gp` for a `<Purse>`; pass day-of-record totals)
- Expedition loot readouts
- Day Report (Spec 1 reuses this component in its treasury footer)

The **stored value remains (g, s, c)** — this is a display-layer change only. No backend work.

## Accessibility

- Element must be focusable via keyboard (`tabindex="0"`) and show the tooltip on focus.
- Tooltip content should also be available to screen readers — wrap the trigger in `<span aria-describedby="...">` and give the tooltip an `id` + `role="tooltip"`.

---

# Design tokens (use these; import from the existing stylesheet)

These are copied from `reference/colors_and_type.css` — use the codebase's existing CSS variables rather than hard-coding hex.

```css
/* Background */
--bg-primary:     #000000;
--bg-secondary:   #0f1419;   /* card surface */
--bg-input:       #111827;   /* input / popover bg */
--bg-card:        #1f2937;   /* elevated card (e.g. Day Report modal) */

/* Borders */
--border-color:   #4b5563;
--border-subtle:  #374151;

/* Accents */
--accent-green:      #4ade80;   /* primary, headings, success */
--accent-green-dark: #22c55e;   /* primary button bg */
--accent-red:        #ef4444;   /* danger, combat */
--accent-blue:       #60a5fa;   /* XP, choice, info */
--accent-gold:       #fbbf24;   /* currency */
--accent-purple:     #a78bfa;   /* Stahl tie-in (rarely used) */

/* Text */
--text-primary:   #f3f4f6;
--text-secondary: #9ca3af;
--text-muted:     #6b7280;

/* Geometry */
--radius:         6px;

/* Type */
font-family: 'JetBrains Mono', 'Cascadia Code', 'Fira Code', Consolas, Monaco, monospace;
```

## Component tokens (from mocks)

- **`.btn`** base: `padding 6px 14px`, `font-size 12px`, `font-weight 600`, `border 1px solid transparent`, `radius var(--radius)`, gap `6px`
- **`.btn-sm`**: `padding 3px 10px`, `font-size 11px`
- **`.btn-primary`**: bg `var(--accent-green-dark)`, color `#000`; hover bg `var(--accent-green)`
- **`.btn-secondary`**: bg transparent, color `var(--text-secondary)`, border `var(--border-color)`
- **`.btn-danger`**: bg `var(--accent-red)`, color `#fff`
- **`.card`**: bg `var(--bg-card)`, border `1px solid var(--border-color)`, radius `var(--radius)`, box-shadow `0 2px 8px rgba(0,0,0,.5)`, padding `14px`

## Animation

```css
@keyframes dayIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
/* Entry reveal: 300ms ease-out, opacity + 4px translateY */
```

---

# Assets

- No new images or icons are introduced.
- Fonts: **JetBrains Mono** (already in the codebase at `/frontend/public/` and `/assets/`).
- No external icon library is used — the mocks use text glyphs only (`⟲`, `▸`, `·`, `→`). Match this: no new lucide/heroicons/feather imports.

---

# Recommended implementation order

1. **Spec 3 (Purse component)** — smallest surface, zero backend work, usable standalone. Ship first to establish the pattern.
2. **Spec 2 (delete-confirm popover)** — small, isolated to the Keep Select view.
3. **Spec 1 (Day Report modal)** — largest. If the backend change is out of scope, ship v1 that aggregates existing notification events client-side, then iterate once the backend returns a structured `DayReport`.

---

# Open questions for the user

- Should the Day Report fully **replace** the existing global notification feed, or coexist during a transition period?
- For the "Dismiss" path (player dismisses without advancing), should the day stay un-advanced indefinitely, or is there a timeout?
- Are there event types beyond the seven listed (`info / combat / loot / choice / healing / upkeep / tavern`) that need their own dot color?

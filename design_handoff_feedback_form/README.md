# Handoff: In-Game Feedback Form (Venturekeep, playtest v0.9.1)

## Overview
A modal feedback form that opens over whatever screen the player is on, so playtesters
can report problems without leaving the game. Entry point is a persistent
**⚑ Submit Feedback** control in the left sidebar footer. The modal captures category,
context, freeform feedback, an optional 4-point importance rating, and (when not signed
in) an optional name. On submit it stores a row in a `feedback` table, shows a brief
"Thanks!" confirmation, clears the form, and offers **Submit Another** — no redirect,
the player goes straight back to playing.

## About the Design Files
The files in this bundle are **design references created in HTML** — a working prototype
of the intended look and behavior, not production code to copy. The task is to
**recreate this design in the Venturekeep codebase** (`karmuno/DungeonEconomist`:
FastAPI backend + Vue 3 + TypeScript frontend) using its established patterns — a Vue
SFC using the existing theme variables in `frontend/src/assets/main.css`, plus a
FastAPI route and model for persistence. Do not port the React/inline-style structure
verbatim; match the visual spec below with the codebase's own components.

## Fidelity
**High-fidelity.** Colors, type sizes, spacing, and interaction states below are final
and should be matched closely. All values come from the Venturekeep design system
(pure-black ground, one phosphor green, monospace only, hairline borders, no gradients
or imagery).

## Screens / Views

### 1. Host screen (context only — already exists)
The dashboard behind the modal is included in the prototype only to show placement.
The one thing to build here is the sidebar footer entry point:

- Section divider: `border-top: 1px solid #374151`, `padding-top: 16px`.
- Eyebrow label: "Playtest", 10px, `#6b7280`, uppercase, `letter-spacing: .12em`.
- Button: secondary variant (transparent fill, `1px solid #4b5563`, text `#9ca3af`),
  size sm (`padding: .25rem .625rem`, `font-size: .75rem`), full width, radius 6px,
  label `⚑ Submit Feedback`.
- Under it, a 10px `#4b5563` status line: `"Found something odd? Tell us."`, replaced
  after submissions by `"N report(s) sent this session"`.

The control must be reachable from **every** screen (including the login screen, where
the user is unauthenticated).

### 2. Feedback modal
Purpose: submit one piece of feedback quickly, repeatedly.

**Shell** (matches the design system `Modal`):
- Fixed overlay, scrim `rgba(0,0,0,0.75)`, centered, `z-index: 1000`. Click scrim = close.
- Panel: background `#111827`, `1px solid #4b5563`, radius 6px,
  shadow `0 0 40px rgba(0,0,0,.8)`, `width: 90%`, `max-width: 560px`,
  `max-height: 85vh`, body scrolls if needed.
- Sticky header: `padding: .625rem 1rem`, `border-bottom: 1px solid #4b5563`.
  Title "Submit Feedback", 1.05rem, 700, `#4ade80`. Right-aligned `×` close button,
  1.25rem, `#6b7280`, `aria-label="Close"`.
- Body padding `1rem`; form is a vertical flex column with `gap: 10px`.

**Field chrome (all fields)**
- Label row: 11px, weight 600, `#9ca3af`, uppercase, `letter-spacing: .06em`,
  `margin-bottom: 4px`. Required fields append a red asterisk `*` in `#ef4444`.
  Optional fields put a right-aligned 10px `#4b5563` uppercase "Optional" tag on the
  same row (`display:flex; justify-content:space-between`).
- Inputs/select/textarea: background `#1f2937`, `1px solid #4b5563`, radius 6px,
  `font-size: .825rem` (textarea 13px), monospace, text `#e5e7eb`,
  placeholder `#6b7280`, `padding: .5rem .75rem`.
- Focus: `border-color: #4ade80` + `box-shadow: 0 0 0 2px rgba(74,222,128,.15)`,
  `outline: none`, transition 0.15s on border-color.

**Fields, in order**

1. **What kind of feedback is this?** — `<select>`, **required**. Custom muted caret
   (SVG chevron, stroke `#6b7280`, right .5rem), `appearance: none`,
   `padding-right: 2.5rem`. Placeholder option `"Choose one…"` with empty value.
   Options (stored verbatim):
   - Something is broken
   - I'm confused or stuck
   - Something feels wrong
   - I have an idea
   - I like something

2. **What were you doing?** — single-line text, **required**.
   Placeholder: `e.g. "Sending my party into the dungeon"`

3. **What's your feedback?** — textarea, **required**, `rows="3"`,
   `line-height: 1.5`, `resize: vertical`. No helper text.

4. **How important is this feedback?** — optional 4-point scale.
   *Note: the v0.9.1 spec listed a five-point severity scale; the playtest team replaced
   it with this 4-point scale and new copy. Build the 4-point version; `severity` stays
   an int 1–4, nullable.*
   - Layout: `display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 8px`.
     Each cell is a vertical flex column, `gap: 4px`: number button, then title, then
     description.
   - Button: full cell width, `height: 38px`, radius 6px, `font-size: 15px`, weight 700,
     content = the number.
     - Default: bg `#1f2937`, text `#9ca3af`, border `1px solid #4b5563`
     - Hover: bg `rgba(74,222,128,.08)`, text `#4ade80`, border `#4ade80`
     - Selected: bg `#22c55e`, text `#000`, border `#22c55e`
     - Transitions: `background-color .12s, border-color .12s, color .12s`. No scale/bounce.
     - Clicking the selected number again clears the rating (back to null).
   - Title under the button: 11px, weight 700, centered, `line-height: 1.3`;
     `#9ca3af` default, `#4ade80` on hover or when selected.
   - Description under the title: 10px, centered, `line-height: 1.35`,
     `text-wrap: pretty`; `#6b7280` default, `#9ca3af` when selected.

   | # | Title | Description |
   |---|-------|-------------|
   | 1 | Barely | I don't care if this issue is ever addressed. |
   | 2 | Somewhat | It would be nice to see this issue get addressed. |
   | 3 | Very | I would have a lot more fun if this issue were addressed. |
   | 4 | Critically | I won't or can't play the game until the issue is addressed. |

5. **Name** — single-line text, optional, **rendered only when the user is not
   authenticated**. Placeholder: `So we can follow up — or leave it blank.`
   When authenticated the submission is associated with the account and this field is
   absent entirely.

**Footer actions**
- Right-aligned row, `gap: 8px`, `padding-top: 2px`.
- `Cancel` — secondary button (transparent, `1px solid #4b5563`, text `#9ca3af`),
  `padding: .5rem 1rem`, `font-size: .825rem` — closes the modal.
- `Submit Feedback` — primary button, bg + border `#166534`, text `#000`, weight 600,
  radius 6px. Disabled state: `opacity: .4`, `cursor: not-allowed`.

### 3. Confirmation state (replaces the form inside the same modal)
- Vertical flex, `gap: 14px`, `padding: 8px 0`.
- Headline "Thanks!" — 1.6rem, 700, `#4ade80`.
- Body line, 13px, `#9ca3af`, `line-height: 1.6`:
  - first submission of the session: "Logged. Keep them coming — every report makes the
    next build sharper."
  - subsequent: "Logged. That is N this session — you are doing the cohort a real favour."
- Receipt card: bg `rgba(74,222,128,.06)`, `1px solid #166534`, radius 6px,
  `padding: 10px 12px`, 11px `#6b7280`. Content:
  `feedback #<id> · <category> · severity <n or —>` — built from a **snapshot of the
  submitted values**, since the form fields are cleared on submit.
- Actions, right-aligned: `Submit Another` (secondary — returns to a blank form) and
  `Back to the Keep` (primary — closes the modal).

## Interactions & Behavior
- Sidebar button opens the modal; `×`, `Cancel`, `Back to the Keep`, and a scrim click
  close it. Closing resets the confirmation state (next open shows the form).
- Submit is disabled until category is chosen and both required text fields are
  non-blank (`trim()`). No inline error messages — gating is the validation.
- On submit: POST the row, then (optimistically) show the confirmation, clear
  `category`, `doing`, `feedback`, `name`, `severity`, and keep a snapshot of
  `{category, severity}` for the receipt line.
- `page_url` is captured from the browser at submit time (`window.location.href`) —
  never asked for.
- If authenticated, attach `user_id` and `keep_id` (null when the player is not inside
  a keep). If not authenticated, `user_id`/`keep_id` are null and the optional `name`
  is used.
- Severity hover previews the highlight; clicking the active number clears it.
- Transitions only on color/border/opacity, 0.12–0.15s. No entrance animation.
- Suggested additions not in the prototype: `Esc` closes the modal, focus moves to the
  category select on open, focus returns to the sidebar button on close, and the form
  should be submit-on-`<form>` so Enter works.

## State Management
Local to the modal component:
- `open: boolean` — modal visibility
- `submitted: boolean` — form vs. confirmation view
- `category: string`, `doing: string`, `feedback: string`, `name: string`
- `severity: number | null` (1–4), `hoverSeverity: number | null`
- `sentThisSession: number` — drives the sidebar counter and the thanks copy
- `lastSubmission: { id, category, severity }` — receipt snapshot

From app/session state: `isAuthenticated`, `user_id`, current `keep_id`.
Data: one POST per submission; no reads. Treat failures with a retry affordance
(not designed — recommend an inline red `#ef4444` line above the actions).

## Schema

`feedback` table (unchanged from the v0.9.1 spec except severity range):

| Column | Type | Notes |
|---|---|---|
| `id` | INT PK | auto-increment |
| `user_id` | INT FK → accounts.id, nullable | null if not logged in |
| `keep_id` | INT FK → keeps.id, nullable | null if not in a keep / not logged in |
| `category` | VARCHAR | one of the five dropdown values, verbatim |
| `doing` | VARCHAR | "What were you doing?" |
| `feedback` | TEXT | "What's your feedback?" |
| `severity` | INT, nullable | **1–4** (null if skipped) |
| `name` | VARCHAR, nullable | only for unauthenticated users |
| `page_url` | VARCHAR | auto-captured from the browser |
| `created_at` | TIMESTAMP | defaults to now |

Endpoint: `POST /api/feedback`, body = the client-supplied columns; server stamps
`user_id`, `keep_id`, and `created_at`. Returns the new `id` for the receipt line.

## Design Tokens
Colors
- Ground `#000000` · card/input `#1f2937` · modal `#111827` · hover wash `rgba(74,222,128,.08)` · tint `rgba(74,222,128,.06)`
- Green: bright `#4ade80` · fill `#22c55e` · dim `#166534`
- Text: primary `#e5e7eb` · secondary `#9ca3af` · muted `#6b7280` · faint `#4b5563`
- Borders: `#4b5563` (controls) · `#374151` (rules) · Danger `#ef4444` · Info `#60a5fa`
- Selection `rgba(74,222,128,.25)` on `#4ade80`

Type — monospace only:
`'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace`
- 1.6rem/700 confirmation headline · 1.05rem/700 modal title · 13px body · .825rem controls
- 11px labels & titles (uppercase labels `letter-spacing: .06em`) · 10px meta/descriptions
  (eyebrows `letter-spacing: .12em`) · 15px severity numerals

Spacing: 2 / 4 / 6 / 8 / 10 / 12 / 14 / 16 / 24px. Radii: 6px controls & cards, 4px badges.
Shadows: card `0 2px 8px rgba(0,0,0,.5)` · modal `0 0 40px rgba(0,0,0,.8)` ·
focus ring `0 0 0 2px rgba(74,222,128,.15)`.
Transitions: 0.12–0.15s on color/border/opacity only.

## Assets
None. The only glyphs used are unicode: `⚑` (sidebar button), `×` (close), `·` (meta
separator), `—` (empty value), and the inline SVG chevron in the select caret. No icon
library, no imagery.

## Files
- `Feedback Modal.dc.html` — the prototype (host dashboard + modal + all states).
  Open it in a browser; the modal is visible by default. Toggle `loggedIn` in the file's
  props to see the unauthenticated variant with the Name field.
- `support.js` — runtime needed to open the prototype locally (not for production).
- `_ds/` — the Venturekeep design tokens and component bundle the prototype loads
  (reference only; the real app already has these values in `main.css`).

# Venturekeep Design System

A design system for **Cody Jane Games**, derived from **Venturekeep** — a retro RPG party-management simulation (manage adventurers, form parties, send them into dungeons, run an economy of gold, XP, and upkeep).

The brief for Cody Jane Games: *games that are simple but human-readable, with a timeless, even "retro" feel, accessible to as many people as possible — clear communication of ideas over fancy graphics.* This system encodes exactly that: a **retro terminal** aesthetic — pure-black ground, a single phosphor-green accent, one monospace family, no decorative imagery, and iconography built from plain unicode glyphs. It reads like a well-lit text terminal, not a glossy game UI.

## Sources

- **GitHub:** [`karmuno/DungeonEconomist`](https://github.com/karmuno/DungeonEconomist) — the Venturekeep codebase (FastAPI + Vue 3 + TypeScript). The shipping theme lives in `frontend/src/assets/main.css`; screens are in `frontend/src/views/`. Explore it to build deeper or more accurate recreations.
- **Live demo:** https://venturekeep.stahlsystems.com/ (experimental; data may reset).

Tokens, components, and the UI kit here were lifted directly from that CSS and those Vue components — hex values, spacing, and copy are faithful to the source, re-expressed as portable CSS custom properties + React.

---

## CONTENT FUNDAMENTALS

How Venturekeep writes copy:

- **Voice — warm, terse, gently archaic game-master.** Short declaratives. It narrates the world to you: *"The expedition is complete!"*, *"A Halfling arrived at the tavern."*, *"Borin Stonefist has fallen in the dungeon."*
- **Person.** Player-facing labels are second person / possessive: *"Your Keeps"*, *"Sign in to your account"*. System events are third-person narration of the world.
- **Casing.** Headings and nav are **Title Case** (*"Active Expeditions"*, *"Switch Keep"*). Form labels, table headers, and badges are **UPPERCASE** with letter-spacing (*KEEP NAME*, *ON EXPEDITION*). Body copy is sentence case.
- **Tone is encouraging and a little theatrical** at high-stakes moments — confirmation buttons read *"Awesome!"*, *"Excellent!"*, *"Delve!"* rather than "OK". Flavor over function in the moments that matter; plain and direct everywhere else.
- **Fantasy flavor, plainly worded.** Domain nouns are evocative (Keep, Tavern, Expedition, Depth, Upkeep, the six classes — Fighter, Cleric, Magic-User, Elf, Dwarf, Halfling) but sentences never get purple. *"Drag adventurers here to unassign them."* is the register.
- **Destructive actions are blunt and honest.** *"This is permanent."* / *"Delete Forever"*. No euphemism.
- **Numbers are concrete and inline:** `Day 12 · 142gp · Temple, Smithy`, `4/6`, `avg Lv 3`, `22/22 HP`, `8200/12000 XP`. The middot `·` separates meta.
- **No emoji in chrome.** Emoji appear *only* as data — magic-item type markers in lists. UI labels never use them.

---

## VISUAL FOUNDATIONS

- **Color.** Pure black `#000` ground (not a dark grey). Surfaces climb in tiny steps — `#111111` hover wash, `#1a1a1a`, `#1f2937` card/input body, `#111827` modal. The brand is carried almost entirely by one **phosphor green** (`#4ade80` bright, `#22c55e` fill, `#166534` dim). Status colors are used sparingly and consistently: **gold** `#fbbf24` (treasure/warning), **blue** `#60a5fa` (expeditions/info), **red** `#ef4444` (danger/death), **purple** `#a78bfa` (parties/metrics).
- **Type.** Monospace only — there is no second family. Stack: `'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace`. Headings are green and 700. The scale is small and dense (body ~13px, meta ~11px, badges ~10px) because the app is information-rich. Big numbers (treasury, game day, stat tiles) are the one place type gets large.
- **Backgrounds.** Flat black. **No gradients, no images, no textures, no patterns.** Depth comes from 1px borders and a single soft drop shadow, never from color washes behind content. Full-bleed imagery is not part of the language.
- **Spacing.** Compact, utilitarian rhythm: 4 / 6 / 8 / 12 / 16 / 24px. Card padding is tight (12–16px). Rows are dense with small gaps. The layout is a fixed 56px header + 260px left sidebar + scrolling main.
- **Borders.** Hairline `1px solid #4b5563` everywhere — cards, inputs, table rules (`#374151`), dividers. Borders, not shadows, do most of the structural work. Unbuilt/placeholder cards use a **dashed** border at 0.7 opacity.
- **Corner radii.** 6px default (cards, buttons, inputs), 4px badges, 3px progress bars and item tags. Nothing is pill-round; nothing is sharp-square.
- **Cards.** Body `#1f2937`, 1px border, `0 2px 8px rgba(0,0,0,.5)` shadow, 6px radius. The domain convention adds a **3px left accent bar** to type a card: green = adventurer, purple = party, blue = expedition. Clickable cards get a faint green wash on hover (`rgba(74,222,128,.04)`).
- **Shadows.** Two only: card `0 2px 8px rgba(0,0,0,.5)` and modal `0 0 40px rgba(0,0,0,.8)`. Plus a green focus halo on inputs: `0 0 0 2px rgba(74,222,128,.15)`.
- **Hover states.** Greens brighten (`#22c55e → #4ade80`); ghost/secondary controls fill with the input surface and text lifts from muted to primary; rows/cards take a translucent green wash. Borders shift toward green or the relevant accent on interactive hover.
- **Press / active.** No shrink or bounce. State is communicated by color: the active tab gets a green underline, the active segmented-toggle button fills solid green with black text.
- **Selection wash.** Text selection is `rgba(74,222,128,.25)` with green text — the phosphor theme even in selection.
- **Animation.** Minimal and mechanical. Transitions are short (0.1–0.15s) on color/border/opacity only. The one looping animation is a 0.7s linear spinner with a green leading edge. **No easing flourish, no bounce, no entrance choreography.** Progress/expedition bars ease width over 0.3s.
- **Transparency & blur.** No blur anywhere. Translucency is used only as flat color tints — green/blue/gold/red at 4–15% alpha for hover washes, badge fills, and notification backgrounds. The modal scrim is 75% black, opaque-feeling.
- **Imagery vibe.** Effectively none. There is a castle wordmark logo and a purple publisher mark; the game itself renders no illustrations or photography. If imagery is ever needed, it should stay incidental — the ideas carry the screen.

---

## ICONOGRAPHY

Venturekeep deliberately **has no icon font and almost no SVG icons in-app** — true to the "human-readable, retro terminal" brief, it leans on **unicode glyphs and emoji** that render in any font:

- **UI affordances are unicode characters:** `☰` (U+2630) drag handle · `▶` / `▼` (U+25B6 / U+25BC) collapse/expand · `×` (close / remove / unassign) · `·` (middot, meta separator) · `—` (em dash, empty value).
- **Emoji appear only as data, never as chrome** — magic-item type markers shown inline next to an adventurer's name (e.g. a weapon/armor/ring glyph + its bonus). Chrome labels and buttons are always plain text.
- **The brand mark** is a blocky **castle wordmark** (`assets/venturekeep-logo.png`, black on white) — the favicon and social-card image. In-app the brand shows as the green monospace wordmark "VentureKeep", not the raster logo.
- **Social icons** (`assets/social-icons.svg`) are an SVG `<symbol>` sprite — bluesky, discord, github, x, plus docs/community marks (the latter in publisher purple `#aa3bff`). Use these only in footers/marketing, referenced via `<use href="social-icons.svg#github-icon">`.
- A secondary **purple publisher mark** (`assets/publisher-mark.svg`) and a generic **isometric hero illustration** (`assets/hero-illustration.png`) are kept for completeness but are off the core game brand (they skew purple, not green) — use with care.

**Rule of thumb:** reach for a unicode glyph before any icon library. If a richer icon is unavoidable, match the minimal, single-weight feel — but the system's intent is that text and glyphs carry the meaning.

> **Fonts:** the brand family **Cascadia Code** (SIL OFL) is declared as a real `@font-face` in `tokens/fonts.css`, served from the Fontsource jsDelivr CDN — the genuine font, no substitution. To self-host for offline/production use, drop the woff2 into `assets/fonts/` and swap the `src` url. The `--font-mono` stack still degrades to locally-installed Cascadia Code / Fira Code / Consolas / Monaco if the CDN is unreachable.

---

## INDEX / MANIFEST

**Root**
- `styles.css` — global entry point (consumers link this); `@import`s the token + font layers only.
- `readme.md` — this guide.
- `SKILL.md` — Agent-Skill front-matter wrapper.

**`tokens/`** — CSS custom properties (all `@import`ed by `styles.css`)
- `fonts.css` · `colors.css` · `typography.css` · `spacing.css`

**`guidelines/`** — foundation specimen cards (Design System tab)
- Colors: surfaces · phosphor green · status accents · text & lines
- Type: type scale · uppercase labels
- Spacing: radii · spacing scale · shadows & focus
- Brand: logo & wordmark · iconography

**`components/`** — reusable React primitives (`window.VenturekeepDesignSystem_78126b`)
- `forms/` — `Button`, `Input` (+`FieldLabel`), `Select`, `Checkbox`
- `data/` — `Card`, `Badge`, `StatCard`, `ProgressBar`
- `feedback/` — `Modal`, `Notification`, `EmptyState`, `LoadingSpinner`
- `navigation/` — `Tabs`, `ViewToggle`

**`ui_kits/venturekeep/`** — interactive recreation of the game app (login → keep select → dashboard → village). See its `README.md`.

**`assets/`** — `venturekeep-logo.png` (castle wordmark) · `social-icons.svg` (sprite) · `publisher-mark.svg` · `hero-illustration.png`.

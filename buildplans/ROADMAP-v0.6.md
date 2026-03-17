# VentureKeep Roadmap — v0.6 and Beyond

Post-v0.5.0 priorities, ordered by player impact.

---

## 1. Make Magic Items Matter

Right now magic items are just names. Give them stats that affect gameplay.

- **Weapons**: +1 to combat strength for the adventurer's party
- **Armor**: +1 HP buffer (absorbs damage before HP is touched)
- Show items on the adventurer detail modal and the expedition launch screen
- Cap at 1–2 items per adventurer
- Items persist through expeditions; lost on death

Small effort, high feel-good. Players will chase items.

---

## 2. Adventurer Detail Overhaul

The adventurer modal is bare-bones. It should be a real character sheet.

- Stats summary: class, level, HP, XP with progress bar
- Magic items equipped (with unequip option)
- Expedition history: expeditions survived, total loot earned, deaths narrowly avoided
- Building assignment status (which building, if any)
- Level-up button more prominent when available
- Death/bankruptcy info for fallen adventurers

This makes players care about individual adventurers — which makes death hurt more.

---

## 3. Dashboard That Tells a Story

The dashboard is just stat cards. It should show:

- Dungeon name + deepest level reached
- Active expeditions with progress bars (day X of Y)
- Village buildings summary (what's built, who's assigned)
- A "what to do next" hint for new players ("Form a party to begin")
- Recent events feed (last few notable things that happened)

---

## 4. Balance Pass

The numbers haven't been tuned since the prototype. Deeper dungeon levels should feel meaningfully harder and more rewarding.

- Loot scaling by dungeon level (currently flat-ish)
- Death rate tuning (too many deaths = frustrating, too few = boring)
- Expedition duration vs. reward curve
- Upkeep cost scaling — is 1cp/XP the right number?
- Monster difficulty by level — should level 6 be terrifying?
- Building bonus tuning (is +1 HP/day healing too weak? Too strong?)
- Magic item drop rate vs. Library bonus

Needs real play data to inform. Playtest at each dungeon level.

---

## 5. Sound + Polish

Small things that make the retro RPG feel come alive.

- Notification sounds (expedition return, death, level up, stairs discovered)
- Transition animations between views
- Hover effects on the dungeon level selector
- Loading skeletons instead of spinners
- Keyboard shortcuts beyond admin console (e.g. spacebar = advance day)
- Favicon and page title updates

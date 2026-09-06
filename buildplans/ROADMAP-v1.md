# VentureKeep Roadmap — v0.7 to v1.0

Post-v0.6.1 release plan. Each version groups workstreams from the v1 scope.

**Status as of 2026-09-06**

| | |
| :--- | :--- |
| Released (tagged, on `main`, deployed demo) | **v0.8.1** (2026-03-26) |
| In progress | **v0.9 — The Polish Release**, on branch `qa` (31 commits ahead of `main`, `VERSION` still `0.8.1`) |
| Done so far in v0.9 | Core UX Overhaul (event modal, economic loop, Village, character sheet); the "witnessed rule" fixes from the Aug 2026 UX audit |
| Next up in v0.9 | Onboarding & Direction (not started); rest of Error Handling & Edge Cases |
| Last commit | 2026-08-23 |

Legend: `[x]` done · `[~]` in progress / partial · `[ ]` not started · `[>]` moved to a later version.

Keep this file honest: when a workstream lands, tick it here in the same commit. Update the status table when a version tags.

---

## v0.7 — The Hardened Adventurer Release — SHIPPED 2026-03-25

Security for real users and class identity that makes adventurers feel distinct.

### Auth Hardening — done
- [x] Rate limiting on login/register (`app/rate_limit.py`)
- [x] Password strength requirements
- [x] Token refresh / expiry improvements
- [x] CORS lockdown for production origins (`CORS_ORIGINS`)
- [x] Session invalidation on password change

### Simplified Class Abilities — done
- [x] Cleric: heal (mid-expedition, from `classes.json`)
- [x] Magic-User / Elf: cast (fires in the combat loop on party initiative)
- [x] Round-based OSE combat replaced the single-roll resolver (see `round-based-combat.md`)
- [x] Class abilities influence expedition outcomes (turn undead, spells, heals at decision points)

### Resurrection System — done
- [x] Temple Tier III: resurrect highest-level dead on return
- [x] Gated on a Cleric assigned to the building
- [ ] Gold cost scaling with level / return-at-penalty — not implemented; folded into the v0.9.4 balance pass if it matters

---

## v0.8 — The Monster Release — SHIPPED 2026-03-26 (v0.8.1 same day)

The dungeon gets deeper, the numbers get real, and there's more to find.

### Auto-Delve Completion — done
- [x] Auto-delve wired end-to-end; bug backlog closed (see `AutoDelveBugs.md`)
- [x] Respects party readiness (silent skip is intentional)
- [x] Death mid-auto-delve: `auto_delve_full` blocks relaunch until the player reconfigures (intentional); wiped parties hidden

### Game Balance Pass — partial
- [x] OSE hit points, treasure tables, spell HD limits, to-hit and morale fixes
- [x] Stairs discovery rebalanced (1.5%/turn + 1%/Dwarf, always-popup)
- [x] Building costs cut to 10% (50/250/1250gp) — provisional, Aug 2026
- [>] Death rate, loot-vs-risk, upkeep scaling, building bonus tuning → **v0.9.4 Targeted Balance Pass**

### More Content — partial
- [x] 100 monsters (full OSE dungeon tables), natural-English names
- [x] Magic item variety: rings, named scrolls, named potions
- [x] Random dungeon level names per world
- [x] Smithy added (Dwarf building) instead of the two below
- [>] Wizard's Tower, Fighter Stronghold → post-v1 unless the v0.9.4 playtest demands them
- [>] Non-combat events (NPCs, puzzles, environmental) → post-v1
- [>] Room flavor text → post-v1

---

## v0.9 — The Polish Release — IN PROGRESS (branch `qa`)

Goal: A new player can understand the game, enter the core loop, and become invested in what happens to their adventurers.

This is your UX release.

### Core UX Overhaul — done
- [x] Adventurer detail modal as a character sheet (stats, XP bar, history, items, upkeep); every adventurer name anywhere opens it
- [x] Expedition progress visualization: Expedition Event modal redesigned per `design_handoff_expedition_event_modal/`, then playtested (Aug 2026)
- [x] Economic loop readable on screen per `design_handoff_economic_loop/`: Upkeep Day modal, sidebar upkeep forecast + at-risk list, Village rebuilt around numbers with click-to-assign
- [x] Village/building UI improvements (same handoff)
- [ ] Responsive layout for mobile — if it fits without derailing the release (2 media queries in the codebase today; effectively not started)

### Onboarding & Direction — not started
First-login flow guiding players through:
- [ ] Recruitment
- [ ] Party formation
- [ ] First expedition
- [ ] Contextual hints
- [ ] "What to do next" suggestions on the dashboard
- [ ] Help/info tooltips on important mechanics

### Error Handling & Edge Cases — partial
- [ ] Graceful handling of known failure modes
- [ ] API error responses with actionable messages
- [ ] Frontend error boundaries and retry logic where appropriate
Handle:
- [~] Empty parties — empty parties disband at end of day with a `party_disbanded` event (audit C11)
- [~] Bankrupt Keeps — debtor's prison / deferred upkeep are modelled and shown on Upkeep Day; the fully-bankrupt Keep path is unreviewed
- [~] All-dead rosters — wiped parties hidden, TPK survivor bug fixed; the empty-roster dashboard state is unreviewed
- [~] Audit critical expedition events and state transitions for silent failure — the **witnessed rule** is now enforced: dashboard, resource counters, phase totals, deaths and stairs all hold until the player has seen the event that caused them (audit C7). Remaining audit findings live outside this repo; pull them in here before calling this done.

That last one should probably be an explicit lesson from the stairs problem:

> Meaningful game events must either resolve correctly or fail visibly.

Then we begin the march through the v0.9.x releases.

---

## v0.9.1 — The Observable Keep — not started

Goal: Understand what players do and what the game does when they do it.

This is where you add instrumentation and better operational visibility.

Already in place, for reuse: a per-keep balance `/metrics` endpoint and MetricsPanel (dungeon-level stats, not player journey), and a typed frontend `eventBus` with metrics events.

### Player Journey
- [ ] Account created
- [ ] Adventurer recruited
- [ ] Party formed
- [ ] Expedition started
- [ ] Expedition completed
- [ ] Building purchased/upgraded
- [ ] Return session
- [ ] Repeat expedition

### Attachment Events
- [ ] Adventurer levels up
- [ ] Adventurer reaches level 2
- [ ] Adventurer dies
- [ ] High-level adventurer dies
- [ ] Party wipe
- [ ] Player continues after a meaningful death

### Operational Visibility
- [ ] Server-side exception logging
- [ ] Visibility into failed API calls
- [ ] Visibility into critical UI failures

The objective:

> Can we see whether players reach the attachment loop, and can we see when the machine breaks?

---

## v0.9.2 — The Survivable Keep — partial (deployment docs only)

Goal: VentureKeep can survive technical failure without destroying player worlds.

### Production Database Confidence
- [ ] Integration tests against Postgres (all tests run on SQLite today)

### Backup & Recovery
- [x] Database backup procedure (nightly `pg_dump` cron, 30-day retention — `docs/DEPLOYMENT.md`)
- [x] Automated backups
- [ ] Documented recovery procedure
- [ ] Successful recovery test

The acceptance criterion is:

> We have intentionally tested restoring VentureKeep from a backup.

### Deployment
- [x] Deployment documentation (`docs/DEPLOYMENT.md`: two-account model, Docker, nginx, HTTPS, update, backups, troubleshooting)
- [ ] Enough information for Future Cody to safely recover the game — depends on the recovery procedure above

---

## v0.9.3 — The Public Keep — not started

Goal: VentureKeep can safely support the first deliberately invited strangers.

### Security
- [ ] Dependency review
- [ ] Authentication-flow review
- [ ] Input validation review
- [ ] Fix obvious production vulnerabilities

### Load & Concurrent Users
- [ ] Test concurrent-user behavior
- [ ] Determine approximately what the VPS can comfortably support
- [ ] Identify obvious bottlenecks
- [ ] Establish a reasonable initial player cohort

### Performance
- [ ] Fix obvious slow queries or major frontend bottlenecks discovered during testing

### Browser Sanity
- [ ] Verify that the game works in the browsers you reasonably expect strangers to use

---

## v0.9.4 — The Final Delve — not started

Goal: Validate the actual player experience before launch.

### Final Playtest

Test the entire intended loop:

Create Account → Recruit → Form Party → Run Expedition → Heal/Reform → Run More Expeditions → Earn Taxes → Invest in a Building

Pay particular attention to:
- State transitions
- Silent failures
- Unrecoverable game states
- Adventurer death
- Recovery after death
- Repeated expeditions
- Building progression

### Targeted Balance Pass

Not "perfectly balance VentureKeep."

Instead:
- Do players survive long enough to become attached?
- Do adventurers level quickly enough for progression to matter?
- Is death sufficiently threatening?
- Is death so common that attachment never forms?
- Does risk feel worth the potential reward?

Inherited from v0.8: death rate by level, loot-vs-risk curve, upkeep scaling (1cp/XP), building bonus tuning, the provisional 10% building costs, magic item drop rate vs. Library, class ability power.

---

## v1.0 — Let Them Delve — not started

Goal: Deliberately invite the first real strangers into VentureKeep.

Feature freeze.

No more polish because "one more thing would be nice."

No new content.

No rebuilding the dungeon.

The question changes from:

"Is VentureKeep ready?"

to:

"What happens when real people play VentureKeep?"

### Launch
- [ ] Invite a deliberately small initial cohort
- [ ] Monitor stability
- [ ] Observe the player journey
- [ ] Collect feedback
- [ ] Watch for evidence of player attachment
- [ ] Track return behavior

### First Economic Experiment

Add the simplest possible voluntary support mechanism.

Something like:

> Enjoying VentureKeep? Support its development.

The goal is not to optimize conversion.

The goal is to discover whether the flywheel can complete its first economic cycle:

Great Machine → Passionate Player → Value → Resources → Better Machine

---

## The Overall Progression

| Version | Question it answers | Status |
| :--- | :--- | :--- |
| **v0.7** | Can strangers log in safely, and do classes feel distinct? | shipped |
| **v0.8** | Is the dungeon deep and real enough? | shipped |
| **v0.9** | Can a new player understand and enjoy VentureKeep? | **in progress** |
| **v0.9.1** | Can we understand what players do? | — |
| **v0.9.2** | Can we survive failure without losing player worlds? | docs only |
| **v0.9.3** | Can we safely invite strangers? | — |
| **v0.9.4** | Does the complete experience hold together? | — |
| **v1.0** | What happens when real people play? | — |

Make it understandable → make it observable → make it survivable → make it public → verify the whole experience → let them delve.

---

## Explicitly Deferred to Post-V1
- Full spell management system
- Parlay / monster reaction table
- Dungeon procedural generation / node navigation
- Followers / henchmen
- Payment integration / legal
- Analytics / telemetry beyond v0.9.1's instrumentation
- Wizard's Tower, Fighter Stronghold, non-combat events, room flavor text (from v0.8)
- Engine extraction into a shared subtree (see `engine-extraction.md`)

## Other documents in this folder
- `ROADMAP-v0.6.md`, `BuildPlans.md`, `MVPBuildPlan.md`, `Prototype.md`, `DesignDoc.txt` — history; superseded by this file.
- `round-based-combat.md` — implemented in v0.7. `AutoDelveBugs.md` — closed in v0.8.1.
- `engine-extraction.md` — future, post-v1.

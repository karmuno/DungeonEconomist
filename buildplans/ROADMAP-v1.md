# VentureKeep Roadmap — v0.9 to v1.0

Three releases between here and the first strangers. Everything that does not make the game
safe to invite 10 people into, or legible enough for them to enter the core loop, waits for
the evidence those 10 people produce.

**Status as of 2026-09-06**

| | |
| :--- | :--- |
| Released (tagged, on `main`, deployed demo) | **v0.8.1** (2026-03-26) |
| In progress | **v0.9 — The Polish Release**, on branch `qa` (`VERSION` still `0.8.1`) |
| Done so far in v0.9 | Core UX Overhaul (event modal, economic loop, Village, character sheet); witnessed-rule fixes from the 2026-08-22 UX audit |
| Next up | The four remaining v0.9 items below, then v0.9.1 Safe to Invite |
| Last code commit | 2026-08-23 |

Legend: `[x]` done · `[~]` partial · `[ ]` not started.

Keep this file honest: when an item lands, tick it here in the same commit. Update the
status table when a version tags. Re-cut 2026-09-06 from a six-gate plan (v0.9, .1, .2,
.3, .4, 1.0) to three; the cut items are in **Post-cohort backlog** below. Rationale: the
Operating Strategy's Phase 1 is "safe to invite 10 strangers plus minimal instrumentation";
the old roadmap had grown that into five releases. Governing strategy lives in the
CodyJaneGames repo (`Company_Operating_Strategy.md`, `Strategy_Reconciliation.md`).

---

## v0.9 — The Polish Release — IN PROGRESS (branch `qa`)

Goal: A new player can understand the game, enter the core loop, and become invested in what
happens to their adventurers.

Governing test, from the audit: every primary screen answers *What just happened? What
changed because of it? What meaningful action can I take next?*

### Core UX Overhaul — done
- [x] Character sheet: stats, XP bar, history, items, upkeep; every adventurer name opens it
- [x] Expedition Event modal redesigned per `design_handoff_expedition_event_modal/`, playtested
- [x] Economic loop per `design_handoff_economic_loop/`: Upkeep Day modal, sidebar forecast and
      at-risk list, Village rebuilt around numbers with click-to-assign
- [x] Witnessed rule enforced: dashboard, counters, phase totals, deaths and stairs hold until
      the player has seen the event that caused them (audit C7)
- [x] Party lifecycle: dead members leave, empty parties disband at end of day (audit C11);
      return copy "[Party] brought back X (Y each)" (B11)
- [x] Building costs cut to 10% (50/250/1250gp), provisional

### Remaining — the red cells only
- [ ] Rewrite all class ability text; replace THAC0 / HD jargon with plain labels or tooltips
      (audit row 15, character sheet)
- [ ] Fix Expedition Summary showing the original end date after an early retreat (row 9)
- [ ] Resolve one expedition's pending decision individually (row 10). Cost-check first; if
      it is more than an evening, move it to the backlog
- [ ] Dashboard empty-state prompts: no adventurers → Recruit · no party → Form a party ·
      idle party → Launch. This *is* the onboarding for v1.0
- [ ] One softlock check: all-dead roster and bankrupt keep. Confirm the player can still
      recruit and continue. Fix softlocks only, no polish

Then one full playthrough (Create Account → Recruit → Form Party → Expedition → Heal → Repeat
→ Upkeep → Build) and tag.

---

## v0.9.1 — Safe to Invite — not started

Goal: *I can intentionally invite 10 strangers without fearing that their arrival destroys
the game or their progress, and I can see what they did.*

Merges the old v0.9.1 Observable, v0.9.2 Survivable and v0.9.3 Public Keep down to their
minimums. Not an analytics project, not a security review, not a load test.

### See when it breaks
- [ ] Server-side exception logging (none exists today): a FastAPI exception handler to a
      log file, or Sentry free tier

### See what players do
- [ ] One `player_events` table and inserts for: account created · adventurer recruited ·
      party formed · expedition started · expedition completed · adventurer died · adventurer
      levelled · building bought/upgraded · return session
- [ ] One admin query or console command that answers: did they enter the core loop, where
      did they leave, did they return, did they reach a death or a level-up

### Don't lose their worlds
- [ ] Run the existing test suite against Postgres: make the test engine read `DATABASE_URL`
      and run once against `docker compose up db`. No new tests. (Integration tests against
      the production engine are a v1 blocker; this is their smallest honest scope)
- [x] Nightly `pg_dump` cron with 30-day retention (`docs/DEPLOYMENT.md`)
- [ ] Restore from a backup once, on purpose. Write the steps into `docs/DEPLOYMENT.md`

### Don't get owned on day one
- [ ] `pip-audit` and `npm audit`; fix criticals only
- [ ] Confirm rate limiting and `CORS_ORIGINS` are actually engaged in production
- [ ] 30-minute smoke in Chrome, Firefox, Safari

### The two links that are the point
- [ ] "Feedback?" link (mailto or form). Someone telling you they loved it is the #1 outcome
- [ ] Buy Me a Coffee link, branded Cody Jane Games. No payment integration

**Not in this release, on purpose:** domain migration. A studio-branded tip link on
`venturekeep.stahlsystems.com` is fine for 10 invited people. Decide the name in an hour on a
weeknight; move the domain after the cohort if there is still a reason to.

**In parallel, weekday hours, not code:** the announcement and the list of 10 people. If the
invite list is not ready when v0.9.1 tags, the roadmap did not matter.

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
- [ ] Invite a deliberately small initial cohort (target: 10)
- [ ] Monitor stability (exception log)
- [ ] Observe the player journey (`player_events`)
- [ ] Collect feedback (the link)
- [ ] Watch for evidence of player attachment
- [ ] Track return behavior

### First Economic Experiment

The Buy Me a Coffee link is live from v0.9.1. The experiment is whether anyone uses it.

> Enjoying VentureKeep? Support its development.

The goal is not to optimize conversion. The goal is to discover whether the flywheel can
complete its first economic cycle:

Great Machine → Passionate Player → Value → Resources → Better Machine

### The decision gate (after the first cohort, stop)

Do not automatically add features. Answer:

- Did anyone love it?
- Did anyone return?
- Did the attachment hypothesis appear true?
- What broke?
- What confused people?
- What did they ask for?

Then choose one: double down on VentureKeep · run another iteration · declare the experiment
successful enough and move to DigitalFootball · pause VentureKeep and preserve the lessons.

The Post-cohort backlog below is decided here, with evidence, not before.

---

## Post-cohort backlog

Everything cut on 2026-09-06. None of it is scheduled. Each item re-enters only if the cohort
shows it matters.

### Cut from v0.9
- Guided first-login tutorial, contextual hints, help tooltips on every mechanic
- Responsive layout for mobile
- Frontend error boundaries and retry logic; actionable API error copy
- Fold Parties and Tavern into the Dashboard (audit Priority 5, IA consolidation)
- Launch Expedition as a first-class dashboard control with depth next to the button (row 6)
- Advance Day / Skip to Event tied to a specific expedition (row 7)
- Re-see an expedition's events after leaving the Summary (row 10)
- Per-adventurer visibility into "Healing" (row 11)
- Assign/unassign to party or building from the character sheet (row 15)
- Highlight which tab is home (row 14); "Form an Adventuring Party" copy (row 5)
- Keep creation feedback beyond the header name (row 5)

### Cut from the old v0.9.1 / v0.9.2 / v0.9.3
- Attachment events beyond death and level-up (high-level death, party wipe, continued after
  a meaningful death) as instrumented events
- Failed-API-call and critical-UI-failure visibility
- New Postgres integration tests (beyond running the existing suite)
- Authentication-flow review, input-validation review
- Load and concurrency testing; VPS capacity estimate; slow-query work
- Full browser matrix

### Cut from the old v0.9.4
- Targeted balance pass: death rate by level, loot-vs-risk, upkeep scaling (1cp/XP), building
  bonus tuning, the provisional 10% building costs, magic item drop rate vs. Library, class
  ability power, resurrection cost. The cohort answers "do players survive long enough to
  become attached"; you cannot

### Open flags (from `Strategy_Reconciliation.md`)
- Brand and studio-branded domain before a *paid* tier ships
- Open-source fork risk under a paid-Keeps model; decide what the license reserves

---

## Shipped

### v0.7 — The Hardened Adventurer Release — 2026-03-25
- Auth hardening: rate limiting, password policy, token refresh, CORS lockdown, session
  invalidation on password change
- Class abilities: Cleric heal, Magic-User / Elf spells in the combat loop, turn undead
- Round-based OSE combat replaced the single-roll resolver (`round-based-combat.md`)
- Temple Tier III resurrection, gated on an assigned Cleric

### v0.8 — The Monster Release — 2026-03-26 (v0.8.1 same day)
- 100 monsters from the full OSE dungeon tables; rings, named scrolls and potions
- OSE hit points and treasure tables; spell HD limits; to-hit and morale fixes
- Stairs as an always-popup event at 1.5%/turn + 1%/Dwarf; wiped parties hidden
- Auto-delve bug backlog closed (`AutoDelveBugs.md`); Smithy added
- Not built, now post-v1: Wizard's Tower, Fighter Stronghold, non-combat events, room flavor text

---

## Explicitly Deferred to Post-V1
- Full spell management system
- Parlay / monster reaction table
- Dungeon procedural generation / node navigation
- Followers / henchmen
- Payment integration / legal; paid Keeps and the rest of the monetization progression
- Analytics beyond `player_events`
- Wizard's Tower, Fighter Stronghold, non-combat events, room flavor text
- Engine extraction into a shared subtree (`engine-extraction.md`)

## Other documents in this folder
- `ROADMAP-v0.6.md`, `BuildPlans.md`, `MVPBuildPlan.md`, `Prototype.md`, `DesignDoc.txt`:
  history, superseded by this file.
- `round-based-combat.md`: implemented in v0.7. `AutoDelveBugs.md`: closed in v0.8.1.
- `engine-extraction.md`: future, post-v1.
- The 2026-08-22 UX audit spreadsheet and Claude Design briefs live in the CodyJaneGames repo
  under `VentureKeep/`. Row numbers above refer to that spreadsheet.

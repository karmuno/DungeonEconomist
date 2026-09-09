# VentureKeep Roadmap — v0.9 to v1.0

Three releases between here and the first strangers. Everything that does not make the game
safe to invite 10 people into, or legible enough for them to enter the core loop, waits for
the evidence those 10 people produce.

**Status as of 2026-09-07**

| | |
| :--- | :--- |
| Released (tagged on `rc`, merged to `main`, deployed to demo) | **v0.9 — The Polish Release** (2026-09-07) |
| Previous release | **v0.8.1** (2026-03-26) |
| In progress | **v0.9.1 — Safe to Invite** |
| Done so far in v0.9 | Core UX Overhaul (event modal, economic loop, Village, character sheet); witnessed-rule fixes from the 2026-08-22 UX audit; class text and jargon rewrite; Tier II+ hidden; upkeep simplified (no deferral); disbanded parties keep their history; early-retreat dates honest on every screen; per-expedition decisions; immediate level-ups with popups and linked names; clickable party status |
| Next up | v0.9.1 Safe to Invite, then v1.0 Let Them Delve |
| Last code commit | 2026-09-07 |

Legend: `[x]` done · `[~]` partial · `[ ]` not started.

Keep this file honest: when an item lands, tick it here in the same commit. Update the
status table when a version tags. Re-cut 2026-09-06 from a six-gate plan (v0.9, .1, .2,
.3, .4, 1.0) to three; the cut items are in **Post-cohort backlog** below. Rationale: the
Operating Strategy's Phase 1 is "safe to invite 10 strangers plus minimal instrumentation";
the old roadmap had grown that into five releases. Governing strategy lives in the
CodyJaneGames repo (`Company_Operating_Strategy.md`, `Strategy_Reconciliation.md`).

---

## v0.9 — The Polish Release — SHIPPED 2026-09-07 (tagged `v0.9` on `rc`)

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
- [x] Class ability text rewritten (2026-09-07, from `class-text-rewrite.csv`): one d20-style
      TO-HIT replaces THAC0 + ATK; HD, LVL, WEALTH, UPKEEP and items carry help text; every
      unlocked ability is listed with its per-expedition uses; Cleric abilities match the sim
      (Turn Undead, Revive, Cure Light Wounds); one spell (Sleep). Combat log reads
      "roll + bonus To-Hit vs Armor Class"; heals, revives (potion or Cleric) and scroll casts
      are logged; HP Healed credits the healer
- [x] Hide Tier II+ building UI (upgrade button, next-tier block, Tier II+ slots and stats)
      until tier slot placement is fixed — see note under Post-cohort backlog. Data and the
      upgrade endpoint stay
- [x] Upkeep simplified: everyone pays on the day, in the dungeon or not; building staff
      exempt. Someone away and short pays what they have and settles the rest on return
      (loot counts); prison only at the gate. Deferred upkeep is gone
- [x] Disbanded parties (last member removed, wiped, or deleted) keep their row and their
      expeditions, so the Expeditions tab keeps the history. Dashboard parties expand
      independently; Dwarves may train at the Training Grounds; retreat and return
      notifications name the party
- [x] Early retreats report the day the party actually came home, not the planned end date
      (row 9). The Summary's PLANNED/ACTUAL block landed with the event-modal redesign;
      2026-09-07 carried `actual_return_day` through to the Expeditions list and the
      expedition detail view, which were both still showing the plan, and added API
      regression tests
- [x] Resolve one expedition's pending decision individually (row 10)
- [x] Level-ups are their own moment: an adventurer advances the instant expedition XP is
      credited rather than at end of day, every level-up raises a popup (not only a new
      keep record), and each queues so several on one day are seen one at a time
- [x] Every notification and popup that names an adventurer links to their sheet. Events
      carry the ids of everyone they name, so the link is exact rather than guessed from
      the text; the expedition choice and summary views now route their events through the
      side panel instead of flattening them to bare strings
- [x] A party's status badge on the Dashboard is a link to what that party is doing:
      Ready or Healing opens Launch Expedition for it, On Expedition opens that
      expedition's summary

### Cut 2026-09-07 — both rested on a false premise
- Dashboard empty-state prompts (no adventurers → Recruit · no party → Form a party) and
  the all-dead / bankrupt softlock check. Both assumed recruitment is a player action with
  a cost. It is not: `run_daily_recruitment` rolls free every day inside `advance_day`, so
  there is no Recruit button to prompt and no state a player can be stuck in. From an empty
  keep the only move is Skip to Event until enough adventurers have arrived to delve, and
  that already works. The real gap they were reaching for — getting from the Dashboard into
  the loop in one click — is the status-badge link above

Then one full playthrough (Create Account → Skip to Event until adventurers arrive → Form
Party → Expedition → Heal → Repeat → Upkeep → Build) and tag.

---

## v0.9.1 — Safe to Invite — IN PROGRESS

Goal: *I can intentionally invite 10 strangers without fearing that their arrival destroys
the game or their progress, and I can see what they did.*

Merges the old v0.9.1 Observable, v0.9.2 Survivable and v0.9.3 Public Keep down to their
minimums. Not an analytics project, not a security review, not a load test.

### Before strangers see it

Widens the goal above: a stranger's first thirty seconds must not look broken, and the
mechanics they meet first must read correctly. Gameplay and UX rather than safety, kept in
this release rather than opening a fourth gate.

- [ ] **The character sheet shows "+1" without saying what it does.** Half-built already:
      `itemHelp()` (`AdventurerDetail.vue:44`) covers **weapon and armor only**, and only as a
      hover `title` — invisible on touch and undiscoverable anywhere. Potion, scroll and
      artifact get no explanation at all. Every effect is defined in `app/magic_items.py`
      (`get_weapon_bonus`, `get_armor_bonus`, `get_scroll_count`, `get_spell_multiplier`,
      `has_potion`) — derive the copy from that module so it cannot drift from the sim.
      **Cody writes the player-facing copy, not Claude** (2026-09-09), same as
      `class-text-rewrite.csv`. Claude's job is to state what each item actually does
      mechanically and wire the strings up.
      Not a defect: `itemBonusLabel()` returning an empty string for potions and scrolls is
      correct — consumables carry no standing bonus. A quantity badge ("how many of this do I
      have") is **future work**, not v1.0
- [ ] **Armor does the wrong thing.** `app/routes/expeditions.py:562` adds the item bonus to
      starting HP as `armor_buffer`, i.e. temporary hit points. Cody's ruling 2026-09-09: it
      should be **either per-attack damage reduction, or a bonus to the wearer's Armor Class**.
      AC is currently uniform and invisible — `app/expedition.py:21` hardcodes `PC_AC = 7`
      ("all PCs in leather-equivalent armor"), so no adventurer differs from another and the
      character sheet never displays it. Taking the AC route therefore also means surfacing AC
      on the sheet and in the combat log, which already reads "roll + bonus To-Hit vs Armor
      Class". Decide which of the two before writing any copy, since the description follows
      the mechanic. The existing tooltip *"Armor: Reduces damage received"* describes the
      intended behaviour rather than the shipped one
- [ ] **The expedition summary never names what was found.** It shows `total_loot` as
      currency only (`ExpeditionSummaryView.vue:173`); magic items appear nowhere, so a
      party can come back with a +2 sword and the screen that reports the delve stays silent
      about it. Pure surfacing, no new systems: `MagicItem` already records
      `found_expedition_id` and `found_day` (`app/models.py:251-252`), so the summary endpoint
      can return the items for that expedition — name, type, bonus, and who is carrying it —
      for the view to render beside the loot line
- [ ] **The Village shows one effect out of twelve, and never says how many slots are left.**
      `assignBonus()` (`frontend/src/views/VillageView.vue:103`) string-scrapes
      `current_stats` for entries containing `"per"` and truncates at `" per "`, then shows the
      result only in the assign popover header — which is why the recruitment bonus is the one
      thing visible. Meanwhile `_get_building_bonuses` (`app/routes/expeditions.py:43`)
      computes twelve: to-hit, damage, morale, magic-item discovery, healing-potion chance,
      resurrect-on-return, scroll craft, artifact crafting and its cost, smithy craft chance
      and slots, masterwork chance. `slotViews()` already draws slots individually but nothing
      states "2 of 3 free". Needed: remaining-slot count per building, and the actual effect of
      assigning someone, stated on the building rather than hidden behind a popover.
      **Land this with the buildings-XP item below** — that replaces the recruitment bonus with
      +10% class XP, so the one effect currently visible is the one about to change
- [ ] **Auth flash and stale-session dashboard.** Two faces of one bug: `router.beforeEach`
      (`frontend/src/router/index.ts:72`) authorises on the *presence* of a `token` in
      localStorage, never its validity. A stale token therefore renders the dashboard, every
      API call 401s, and only a refresh lands on the login screen; and a logged-out visitor
      with leftover storage sees a flash of dashboard first. Fix: validate the session before
      the first navigation resolves, hold the first render behind that check, clear the token
      and redirect on 401
- [ ] **Buildings grant XP, not recruitment.** Replace the `recruitment_bonus` flag
      (`app/buildings.py:103`; four buildings in `app/data/buildings.json`) with **+10% XP
      gain for the building's relevant class**. Recruitment is already free and automatic, so
      the current bonus buys nothing a player can feel. Needs a new bonus key threaded through
      `_get_building_bonuses` (`app/routes/expeditions.py:43`) into `app/progression.py`.
      The +10% is provisional, like the 10% building costs. **Pairs with the Village legibility
      item above:** removing the recruitment bonus removes the only effect the Village
      currently displays, so shipping one without the other leaves that panel showing nothing
- [ ] **Auto-delve is one checkbox.** `auto_delve_healed` and `auto_delve_full`
      (`app/models.py:177-178`) **stay separate in the backend** — the one checkbox sets both,
      so they can be split again later without a migration. Tooltip: *"Party will
      automatically start an expedition when it has 6 fully-healed members."* Move
      `auto_delve_level` off the party settings and onto the **Delve** screen as
      **"Auto-delve to this level"**, offered after a party is formed. No schema change
- [x] **Tavern roster empty while adventurers exist.** Reported 2026-09-09. **Root cause:**
      the Tavern calls `adventurersApi.list(true)` (`AdventurersView.vue:106`) — i.e.
      `include_all=true` — so `list_adventurers` (`app/routes/adventurers.py:100`) skips its
      dead/bankrupt SQL filter and returns the first 100 rows of *everyone*, unordered, which
      is the 100 **oldest** adventurers. In a keep whose IDs have reached #925 those are
      almost all dead or bankrupt, and the client-side status filter then drops every one,
      leaving an empty roster. Party Formation and Parties call `list()` without the flag, so
      the backend filters in SQL and their lists look right — which is why the same
      adventurers show up there. **Fix:** the Roster tab has its own Graveyard and Debtor's
      Prison tabs backed by separate endpoints, so it never needs the dead — drop the `true`.
      The 100-row cap stays latent for any keep with 100+ *living* adventurers; paginate or
      filter server-side if that becomes real
      **Fixed 2026-09-09:** Roster fetches living only; `list_adventurers` orders newest
      first; Graveyard and Debtor's Prison order by `death_day` / `bankruptcy_day` descending;
      Dead and Bankrupt dropped from the Roster's status filter (both have their own tabs) and
      `Assigned` added to the default so the roster shows every living adventurer.

### See when it breaks
- [x] Exception logging on **both** sides: **Sentry**. Backend `sentry-sdk[fastapi]==2.69.1`
      in `app/main.py`; frontend `@sentry/vue` in `frontend/src/main.ts` (2026-09-09), its own
      project and DSN, errors only — no tracing, no session replay. Both gate on a DSN being
      set, so local dev reports nothing. Both tag `release` with the same build string
      (`app/version.py` mirrors `vite.config.ts`), so an error names the build it came from and
      "did my fix land?" is answerable. `FastAPI(version=...)` now reads the same source
      instead of a hardcoded `0.8.1`. **Frontend needs `VITE_SENTRY_DSN` set wherever the
      bundle is BUILT** — Vite inlines it — see `.env.example`.
      Not done: source-map upload, so production traces name minified lines. Vue component
      names and breadcrumbs still come through; add `@sentry/vite-plugin` if that isn't enough

### See what players do
- [x] **Graveyard and Debtor's Prison get the Roster's filters** (2026-09-09, Cody): search,
      class and sort-by, with no status control since each tab holds exactly one status. The
      Roster's filter and sort logic was factored into one `applyFilters` used by all three
      tabs rather than triplicated. Every tab sorts on every field its own data carries —
      shared: name, level, class, XP, wealth (normalised to copper), to-hit, HD; Roster adds
      party and HP; Graveyard adds **Died** (`death_day`) and sorts "Party" on
      `death_party_name`, the party they died with; Debtor's Prison adds **Bankrupted**
      (`bankruptcy_day`) and HP, and drops Party entirely. Null numerics sort to the bottom
      descending, so "newest first" puts unknown dates last
- [ ] One `player_events` table and inserts for: account created · adventurer recruited ·
      party formed · expedition started · expedition completed · adventurer died · adventurer
      levelled · building bought/upgraded · return session
- [ ] **A party wipe records how it happened** (Cody, 2026-09-09): the monster type and the
      number of them that did it, plus the party's **average level at the time of the wipe**.
      A TPK is the sharpest attachment signal the cohort can produce, and "they died" without
      what killed them or how outmatched they were answers none of the questions the decision
      gate asks. Capture it on the wipe event, not by reconstruction afterwards — levels and
      party membership change once the dust settles
- [ ] One admin query or console command that answers: did they enter the core loop, where
      did they leave, did they return, did they reach a death or a level-up

### Don't lose their worlds
- [ ] Run the existing test suite against Postgres: make the test engine read `DATABASE_URL`
      and run once against `docker compose up db`. No new tests. (Integration tests against
      the production engine are a v1 blocker; this is their smallest honest scope)
- [x] Nightly `pg_dump` cron with 30-day retention (`docs/DEPLOYMENT.md`)
- [ ] Restore from a backup once, on purpose. Write the steps into `docs/DEPLOYMENT.md`

### Don't get owned on day one
- [ ] Move Python deps to a `[project]` table in `pyproject.toml` with a real `uv.lock`
      (dev tools in a `dev` group); Dockerfile and README install from the lock. Today's
      `uv.lock` is a phantom: no `[project]` table, so `uv sync` installs nothing
- [ ] `pip-audit` and `npm audit` against that lock; fix criticals only
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

### Deferred 2026-09-09
- Pagination on the Tavern's three tabs. `list_adventurers` still caps at 100 rows, so a keep
  with 100+ *living* adventurers silently truncates — now ordered newest-first, so it degrades
  gracefully instead of showing an empty screen. Graveyard and Debtor's Prison have the
  opposite problem: both are unbounded `.all()` queries that run `add_progression_data` over
  every dead or bankrupt row on each load. Neither is a cohort risk — ten strangers start at
  zero adventurers — and both bite a long-lived keep. Re-enters if a cohort player approaches
  100 living adventurers, or when graveyard load time becomes noticeable

### Cut from the old v0.9.1 / v0.9.2 / v0.9.3
- Attachment events beyond death and level-up (high-level death, party wipe, continued after
  a meaningful death) as instrumented events
- Critical-UI-failure visibility — **error boundaries only.** Still cut: a component that
  throws mid-render is reported to Sentry but leaves the player on a blank or half-drawn
  screen with no way forward. `onErrorCaptured` plus a fallback view is real UI work, and a
  cohort of ten can reload.
  **Failed-API-call reporting is done (2026-09-09), not cut.** `request()` in
  `frontend/src/api/client.ts` reports 5xx responses and network failures to Sentry before
  throwing, which covers all 36 bare `catch {}` blocks at once without touching them — they
  keep showing their friendly notifications. 4xx is deliberately not reported: it would bury
  the signal under expected validation errors and 401s the refresh flow already handles.
  Reversed because every bug found in the 2026-09-09 pass — the auth flash, the empty Tavern
  — was frontend, and a backend-only Sentry would have seen none of them
- New Postgres integration tests (beyond running the existing suite)
- Authentication-flow review, input-validation review
- Load and concurrency testing; VPS capacity estimate; slow-query work
- Full browser matrix

### Cut from the old v0.9.4
- Targeted balance pass: death rate by level, loot-vs-risk, upkeep scaling (1cp/XP), building
  bonus tuning, the provisional 10% building costs, magic item drop rate vs. Library, class
  ability power, resurrection cost, and the provisional +10% building XP bonus added to
  v0.9.1. The cohort answers "do players survive long enough to
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
- Retirement bonuses (Temple, Training Grounds, Library, Smithy): `retire_bonus_desc` in
  `buildings.json` is flavor text only, not wired to any effect — `retired_adventurer_id` is
  just a FK recording who retired where. Only the assigned-staff tier bonuses are implemented
- Real 3-tier building implementation with actual tier slots. Today `max_assigned` /
  `min_adventurer_level` per tier (`app/buildings.py` `get_tier_slots`) only gate who can be
  *assigned* (`can_assign_new`'s greedy bottom-up fill); the Tier II/III bonus math in
  `app/routes/expeditions.py` (`_get_building_bonuses`) re-derives "who counts" by scanning
  `assigned_adventurers` for a level floor, with no idea which nominal tier slot anyone
  occupies. Needs an actual occupied-tier field per assignment (not just a level check) so a
  building's total assigned count can't blow past its Tier II/III slot count for bonus
  purposes. Tier II+ UI hidden in v0.9 pending this (see above)

## Other documents in this folder
- `ROADMAP-v0.6.md`, `BuildPlans.md`, `MVPBuildPlan.md`, `Prototype.md`, `DesignDoc.txt`:
  history, superseded by this file.
- `round-based-combat.md`: implemented in v0.7. `AutoDelveBugs.md`: closed in v0.8.1.
- `engine-extraction.md`: future, post-v1.
- The 2026-08-22 UX audit spreadsheet and Claude Design briefs live in the CodyJaneGames repo
  under `VentureKeep/`. Row numbers above refer to that spreadsheet.

# VentureKeep Roadmap — v0.9 to v1.0

Three releases between here and the first strangers. Everything that does not make the game
safe to invite 10 people into, or legible enough for them to enter the core loop, waits for
the evidence those 10 people produce.

**Status as of 2026-09-15**

| | |
| :--- | :--- |
| Released (tagged on `rc`, merged to `main`, deployed to demo) | **v0.9 — The Polish Release** (2026-09-07) |
| Previous release | **v0.8.1** (2026-03-26) |
| In progress | **v0.9.1 — Safe to Invite** |
| Done so far in v0.9 | Core UX Overhaul (event modal, economic loop, Village, character sheet); witnessed-rule fixes from the 2026-08-22 UX audit; class text and jargon rewrite; Tier II+ hidden; upkeep simplified (no deferral); disbanded parties keep their history; early-retreat dates honest on every screen; per-expedition decisions; immediate level-ups with popups and linked names; clickable party status |
| Next up | The 2026-09-19/20 safety list (admin query, Postgres suite, restore drill, `[project]`/`uv.lock`, audits, rate limiting and CORS, deploy, playthrough, tag). Stretch pushes 1 and 2 are done; Push 3 Polish remains |
| Last code commit | 2026-09-15 |

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

**Scheduled across two weekends** (Cody, 2026-09-09) rather than cut, since the release grew
a v1.0 blocker.

**2026-09-12/13 — make it true.** The ghost-adventurer fix first, because it corrupts every
other measurement; then `player_events` with TPK capture, the auth-flash guard, the feedback
form and the Buy Me a Coffee link. Clean baseline taken 2026-09-14 on keeps "New Balance
Test" and "New Balance Test Again" pooled (1401 days, 149 delves, all buildings standing):
**96.9% dead, 0.5% ever reached level 2, median 43 XP per member per delve against 2000
needed**. Recorded as `BASELINE` in `scripts/balance_stats.py`, which now takes `--keep`
(repeatable, to pool).

**2026-09-19/20 — make it safe and ship.** The admin query, Postgres suite run, restore drill,
the `[project]`/`uv.lock` migration and audits, rate limiting and CORS confirmed, then deploy,
full playthrough and tag.

The admin query is deferred because it is the only item here not needed until players are
already playing — `player_events` records from the moment v0.9.1 deploys, so the query can be
written mid-cohort and still see every event. Sketch the four queries while designing the
table anyway: writing them is how you find out the schema cannot answer them.

The legibility items that were to fill the remaining time have all landed; what fills it
now is the **Stretch goals** block at the end of this release, three pushes in priority
order. None of them block inviting anyone.

### Before strangers see it

Widens the goal above: a stranger's first thirty seconds must not look broken, and the
mechanics they meet first must read correctly. Gameplay and UX rather than safety, kept in
this release rather than opening a fourth gate.

- [x] **The character sheet says what each item does** (2026-09-15). Every item carries a
      `description` built from `descriptions` in `app/data/magic_items.json`, with `{bonus}`
      filled in, and the sheet prints it under the item rather than hiding it in a hover
      title. Copy is Cody's (potion and scroll, 2026-09-15; the rest approved as written). A
      quantity badge stays future work
- [x] **Armor is damage reduction** (Cody, 2026-09-15): each hit taken does the armor's
      bonus less damage, to a floor of 0; rings count as armor. The temporary-hit-point
      buffer at launch is gone. Armor Class stays uniform and undisplayed
- [x] **The expedition summary names what was found** (2026-09-15): the completed summary
      returns the magic items whose `found_expedition_id` is the delve, with holder, and the
      view lists them beside the loot with the holder's name linking to their sheet
- [x] **The Village shows every effect and how many slots are left** (2026-09-12). Each
      building row now states what the building delivers right now beside the per-unit rate
      it is built from — "+2" next to "+1 each" — plus a Slots row ("2 free") and the standing
      XP bonus. The API computes totals per tier from who is actually assigned
      (`_stat_lines` in `app/routes/buildings.py`, shared by the Dashboard's effect tag via
      `building_effects`); the view no longer string-scrapes for "per". Tier II+ stays hidden
- [x] **Number appearing trimmed at the lethal end** (Cody, 2026-09-15). Every depth-1
      monster at or above 1.0 deaths per fight in the all-time ranking was re-rolled against a
      fresh level-1 party with the real combat resolver (`scripts/number_appearing_sweep.py`,
      500-1000 fights per candidate) and set to the dice that land in the Goblin/Orc/Skeleton
      band of 0.7-0.85 deaths per fight: Wolf 2d6→1d3, Halfling 3d6→2d4, Kobold 4d4→2d4,
      Troglodyte 1d8→1d3, Sprite 3d6→2d4, Giant Gecko 1d3→1, Fire Beetle 1d8→1d6, Killer Bee
      1d10→1d8, Rock Baboon 2d6→1d3. OSE's dungeon numbers assume reaction rolls and evasion
      the simulator does not model; these are provisional until it does
- [x] **A magic weapon is to-hit and damage, per OSE** (Cody, 2026-09-14). The launch used to
      hand the simulator level + weapon bonus as one number, so a +1 weapon also raised
      hit dice, a Cleric's cures, revivals and turn attempts, and a caster's spells. The
      weapon bonus now travels on its own and lands only on to-hit and damage. Found on the
      way: the simulator's initialisation overwrote the to-hit bonus the launch had passed
      from the Training Grounds with the class's own, so the building's to-hit had never
      reached a fight; the three now sum
- [x] **Every adventurer named in an expedition view opens their sheet** (Cody, 2026-09-14):
      the summary's member rows, the event popup's rows, the decision page (which now lists
      the party with class, level and HP), and every name in the log tree's prose, through
      one `LinkedText` component fed by the roster's ids, so a party named after an
      adventurer is never mistaken for one
- [x] **The sheet's XP bar reads total XP against the next threshold** while its fill shows
      progress within the current level (Cody, 2026-09-14)
- [x] **XP goes to those who come home** (Cody, 2026-09-14). Everything a run earned —
      fights won and treasure found in the turns actually played — is one pool, split evenly
      among the survivors at the end of the delve. The dead take nothing; a wipe earns
      nothing; a fight the party runs from pays for the monsters killed before running and
      nothing for the rest (2026-09-15). Finalization sums the log it already
      truncates on a retreat, so the even split by launch headcount, which paid the dead a
      full share of everything, is gone
- [x] **Parties retreat instead of dying** (2026-09-09, Cody). Party morale was hardcoded to
      **11**, so a 2d6 check failed only on a 12: 2.8% per check, ~5.5% per lethal combat,
      against a bestiary whose own morale runs 7-9. Parties fought to the death. Now
      `PARTY_MORALE = 7` (`app/expedition.py`), which fails 41.7% per check. Evidence: of 969
      adventurers across 468 expeditions, 793 died and **773 of those deaths were at level 1**
      — 3.9% ever reached level 2. A rout also no longer forfeits recovery: the potion
      auto-revive and the Cleric heal now fire even when the party flees. XP stays 0 on a
      flee, as before. **Cleric revival fires on a rout too** (Cody, 2026-09-09): the
      revival is an abstraction for the Cleric reaching an ally *before* they die, not for
      raising a corpse afterwards, so running away does not undo it. All three post-combat
      recovery steps now behave the same way
- [x] **Dead adventurers fight in later expeditions.** Confirmed 2026-09-09 in Cody's save:
      Faust Anvilstrike, Tinariel Overhill and Audild Phoenixash died on **day 2** (expedition
      891, a Sprite rout) and all three fight in **expedition 892 on day 35** — casting spells,
      being targeted, Faust slain a second time.
      **Cause:** the roster is right and the simulation input is wrong. In the save all three
      are `is_dead` with `death_day = 2`, and expedition 892's `expedition_logs` name six
      living members, none of them the dead; only 892's stored `simulation_data` contains
      them. `launch_expedition` (`app/routes/expeditions.py:707`) searches the process-global
      `simulator.parties` for a cached party whose **first member's id** matches and reuses
      it, so the simulation runs against the roster as it stood at that party's first launch:
      the dead, at their original HP, level and items. `starting_hp` and
      `_finalize_expedition` both read the live `party.members`, which is why the sim's names
      and the logs disagree. `_auto_launch_expedition` (`:578`) registers a fresh party every
      launch and is unaffected. The lookup has been there since the 2026-03-12 refactor.
      **Fix:** register a fresh simulator party on every manual launch, as the auto path
      already does, and delete the lookup. API-level regression test: launch, retreat with
      deaths, relaunch with the same first member, assert the simulated roster equals
      `party.members`.
      **Fixed 2026-09-12:** `launch_expedition` registers a fresh simulator party every
      launch; the lookup is gone. Regression test `test_relaunch_simulates_the_current_roster`
      in `tests/test_main_utils.py` fails against the old code (2 members simulated, 3 in the
      party) and passes now.
      **v1.0 blocker.** A ghost soaks attacks, deals damage,
      casts spells and counts toward party size, so every fight they appear in has the wrong
      odds in an unknown direction, and the death moment lands on the wrong fight.
      **Balance data is contaminated beyond deaths:** every manual relaunch with an unchanged
      first member also ran at stale HP, level and items. Auto-delve launches were clean.
      Measure again only on expeditions generated after the fix.
- [x] **Auth flash and stale-session dashboard.** Fixed 2026-09-12. `router.beforeEach`
      now asks the server (`/auth/me`, through the auth store's shared `ensureSession`)
      before any non-public route resolves, and `main.ts` mounts the app only once the first
      navigation has settled, so nothing paints until the session is known good or gone. An
      unrecoverable 401 mid-session clears the store and routes to login in place instead of
      forcing a full reload. Also fixed on the way: the API client refused to refresh on any
      `/auth/` URL, which included `/auth/me`, so a reload more than 30 minutes after the last
      request logged the player out even with a valid refresh token; only login, register and
      refresh are exempt now. Verified in the browser: no token, a garbage token, a valid
      pair, and a stale access token with a valid refresh token all land where they should
      with the dashboard never loaded
- [x] **Buildings grant XP, not recruitment** (2026-09-12, Cody). Each standing building
      grants **+10% expedition XP** to every class it serves (`xp_bonus` in
      `app/data/buildings.json`, replacing `recruitment_bonus`), applied when XP is credited
      in `_finalize_expedition`. Bonuses **stack across buildings**: an Elf with a Training
      Grounds and a Library gets +20%, a Dwarf with a Training Grounds and a Smithy likewise.
      Provisional, like the 10% building costs; tune after the cohort. Recruitment rolls at
      the flat rate for every class now. **Balance data before this change is not comparable
      with data after it**
- [x] **Auto-delve is one checkbox** (2026-09-15). On Parties and on the Dashboard party
      cards one checkbox sets `auto_delve_healed` and `auto_delve_full` together (both stay in
      the backend), with the tooltip *"Party will automatically start an expedition when it
      has 6 fully-healed members."*, beside the existing depth select. The same control is
      replicated on the Delve screen as **"Auto-delve to this level"**: checking it turns
      auto-delve on and points it at the selected level, unchecking clears the level. No
      schema change
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
- [x] One `player_events` table and inserts per `buildplans/player-events-spec.md`: 16 event
      types from account creation through party wipe, one helper, no separate commit
      (2026-09-12; migration `d5e1f2a3b4c6`, `app/player_events.py`)
- [x] **A party wipe records how it happened** (Cody, 2026-09-09): the monster type and the
      number of them that did it, plus the party's **average level at the time of the wipe**.
      A TPK is the sharpest attachment signal the cohort can produce, and "they died" without
      what killed them or how outmatched they were answers none of the questions the decision
      gate asks. Capture it on the wipe event, not by reconstruction afterwards — levels and
      party membership change once the dust settles
- [x] One admin query or console command that answers: did they enter the core loop, where
      did they leave, did they return, did they reach a death or a level-up. `scripts/gate_queries.py`
      (2026-09-19): reads whatever `DATABASE_URL` points at, prints a per-account summary
      (first `expedition_started`, completed-expedition and return counts, first death/level-up,
      wipe count), a last-event-per-account "where did they leave" report, every TPK in full, and
      `--username` for one account's whole timeline. Aggregated in Python over one pass of
      `player_events` rather than dialect-specific SQL, so it runs unchanged against SQLite or
      Postgres. Verified against the live dev database (13 accounts, one active cohort member)

### Don't lose their worlds
- [x] Run the existing test suite against Postgres (2026-09-19): `tests/test_main_utils.py` now
      reads `DATABASE_URL`, falling back to the SQLite file exactly as the app does. Ran once
      against `docker compose up db` and found two real gaps SQLite's laxity had been hiding,
      both fixed rather than worked around:
      **(1)** `parties.current_expedition_id` and `expeditions.party_id` form a two-way FK
      cycle. The initial migration already breaks it with a deferred, named
      `ALTER TABLE ... ADD CONSTRAINT fk_parties_current_expedition_id`, but the SQLAlchemy
      model never matched that with `use_alter=True` — harmless for migrated databases, but
      `Base.metadata.drop_all()` (the test fixture's teardown, on any backend) can't sort the
      cycle without it, and errors on Postgres where SQLite just warns and moves on. Fixed in
      `app/models.py`, naming the constraint identically to the migration so nothing drifts.
      **(2)** Every `player_events` insert carries an `event_type_id` FK to `event_types`, seeded
      by the production migration but never by `Base.metadata.create_all()`. SQLite doesn't
      enforce the FK, so tests never needed the seed; Postgres does, and the entire
      player-events test surface failed until the fixture called the existing
      `seed_event_types()` helper (`app/player_events.py`, written for exactly this and never
      wired in). With both fixed, all 108 tests pass identically against SQLite and Postgres.
      No new tests, per scope
- [x] Nightly `pg_dump` cron with 30-day retention (`docs/DEPLOYMENT.md`)
- [x] Restore from a backup once, on purpose (2026-09-19): drilled against local
      `docker compose up db` — seed, `pg_dump | gzip`, drop the schema to simulate total loss,
      restore, confirm the data came back exact. Steps in `docs/DEPLOYMENT.md`

### Don't get owned on day one
- [x] Move Python deps to a `[project]` table in `pyproject.toml` with a real `uv.lock`
      (2026-09-19). `[project.dependencies]` holds production deps, `[dependency-groups] dev`
      holds `pytest`/`httpx`; `[tool.uv] package = false` since this is an application, not a
      library. `requirements.txt` is gone — nothing referenced it once the Dockerfile and
      README moved. Dockerfile now bases on `python:3.13-slim` (was 3.11, quietly drifted from
      `.python-version`/`uv.lock`'s `>=3.13` — the phantom lock had been masking a real
      version mismatch), copies the static `uv` binary pinned to match the installed version,
      and runs `uv sync --frozen --no-dev` instead of `pip install -r requirements.txt`.
      Verified by building the image and running it against a fresh `docker compose up db`
      Postgres end to end: migrations to head, `uvicorn` serving on the `uv`-synced venv,
      HTTP 200 with the real frontend bundle. README's install step is `uv sync`
- [x] `pip-audit` and `npm audit` against that lock (2026-09-19). `pip-audit` (via
      `uv export --all-groups` piped in, since it doesn't read `uv.lock` directly) found 14
      findings in 3 packages: `python-multipart` (four DoS advisories parsing crafted
      multipart/urlencoded bodies — reachable from any endpoint that accepts form data,
      bumped 0.0.22 → 0.0.31, the fix version covering all four), `pytest` (local
      `/tmp` predictable-path issue, dev-only and not shipped, bumped to 9.0.3 anyway), and
      `ecdsa` (Minerva timing-attack on P-256 signing — a transitive dep of
      `python-jose[cryptography]`; the app signs JWTs with HS256 only (`app/auth.py`), never
      touching ecdsa's signing path, and upstream has declared side-channel attacks
      out of scope with no planned fix, so this is accepted as unreachable rather than fixed).
      `npm audit` couldn't run: npmjs.org's audit endpoint was down for maintenance
      (503) at the time — worth a re-run once it's back
- [ ] Confirm rate limiting and `CORS_ORIGINS` are actually engaged in production
- [ ] 30-minute smoke in Chrome, Firefox, Safari

### The two links that are the point
- [x] In-game feedback form per `buildplans/feedback-form-spec.md` and the
      `design_handoff_feedback_form/` handoff (2026-09-12): a modal reachable from every
      screen — sidebar footer, and under the form on the auth pages — with the 4-point
      importance scale, its own `feedback` table (migration `e6f2a3b4c5d7`), a receipt line
      and a per-session counter. Someone telling you they loved it is the #1 outcome.
      Verified in the browser from the login screen as a visitor; the signed-in path
      (account and keep attached, no name field) is covered by API tests
- [x] Buy Me a Coffee link to https://buymeacoffee.com/codyjanegames (2026-09-12): the gold
      chip from `design_handoff_bmc_chip/`, in the sidebar footer under Submit Feedback,
      above the version line. No payment integration

### Stretch goals — three pushes, in this order

Fill whatever remains of the 2026-09-19/20 weekend once the safety list above is done. None
of these block inviting anyone. Each push ships whole before the next starts; whatever has
not landed when v0.9.1 tags waits for the decision gate, since v1.0 is a freeze.

**Push 1 — Alignment.** First because the Village below the fold makes dragging adventurers
onto buildings barely usable.

- [x] **Village beside the roster** (2026-09-15). The Dashboard's middle band is two
  independent column stacks: left holds Unassigned Adventurers with the Village card (both
  the populated and the empty state) directly beneath, right holds Parties. Assigning to a
  building is a drag between neighbours, never a drag while scrolling. Parties spans both
  grid rows and the second row absorbs the extra height, so a tall Parties card never
  opens a gap above the Village. Below 1280px viewport the cards stack in one column:
  Unassigned, Parties, Village. The Village header row keeps a fixed name track so the
  assigned count sits beside the name, and its effects wrap instead of truncating
- [x] **Adventurer rows line up in columns** (2026-09-15). Every adventurer row on the
  Dashboard (unassigned, party members, building staff), Parties, Party Formation and the
  Delve screen is a CSS Grid with fixed tracks sized from measured cell widths, keeping the
  `<div>` structure and the drag handlers. Items sit in their own fixed cell after the name
  and wrap onto a second line in the rare four-plus case; a list where nobody carries an
  item, or no row has a remove button, collapses that track so the name gets the room. Names
  wrap rather than truncate, so they are always whole, and so do XP and wealth, at their
  spaces, rather than widening their track. The Dashboard's party header row is a grid too
  (Cody, 2026-09-15): the status badge used to push capacity and average level around, and
  would have again at level 10

**Push 2 — Expedition — DONE 2026-09-15.** Second because both make the expedition views
answer *what just happened?* truthfully.

- [x] **The live expedition summary shows healing per member** (2026-09-15). A member row
  could read a loss next to full health — "-4" beside "6/6 HP" — which looks like a bug and
  is not one: `_replay_member_hp` applied attack damage, then revivals, then
  `healed_adventurers`, so the *final* HP was right and the damage figure was computed from
  the other half of the story with the healing invisible between them. The replay is now
  `_replay_members` and returns `damage_taken`, `hp_healed` and `revived` alongside the HP;
  both summary builders put the three on every member row. The event modal's This Event
  table tallies healing **received** in the current turn beside the damage taken in that
  same turn, so the arithmetic closes: took 4, healed 4, ended 6/6. The So Far ledger keeps
  crediting the healer. Found on the way: the completed summary replayed `party.members`,
  but the dead are detached from their party at finalization, so every casualty came back
  having taken no damage — it replays who actually went out instead
- [x] **The round log replays one ordered event list** (2026-09-15). `resolve_combat_rounds`
  appends to one `events` list per round as each thing resolves — `turn_undead`, `spell`,
  `attacks` (tagged with the side that made them), `morale` — and post-combat recovery is
  appended to the last round fought. The renderer plays that list back, which closed all
  three known misreadings at once: the spell above the monster attacks that preceded it on a
  monsters-first round, turn undead after the spell though it resolves before everything,
  and heals and revivals hanging off the end of the combat. **The simulation was correct in
  every one; only the log misrepresented it.** The renderer also no longer infers a side by
  looking the attacker up in `pcNames`, so a monster named after an adventurer is not
  mistaken for one. Verified in the browser on a fresh delve: round 2 (monsters first) now
  lists six Wolf attacks above Sleep, where the same fight forced back into the old bucket
  shape still lists Sleep first. Expeditions stored before this keep their buckets and still
  render — `roundAttacks` / `roundSpellCasts` / `roundMoraleChecks` normalise either shape
  for the ledger and the replay

**Push 3 — Polish.** Third because it is just that.

- [ ] **Monsters need a plural form and an article.** Singular combat reads "Your party fought
  Goblin."; it should read "a Goblin" / "an Ogre". Plurals are already handled, badly, by a
  heuristic in `app/expedition_events.py:169-175` — `f`/`fe` becomes `ves`, everything else
  gets `s` — which is right for Dwarf, Wolf, Elf and Werewolf but produces **"Robber Flys",
  "Harpys", "Ochre Jellys" and "Mummys"**. Note the same block appears twice in that file
  (`:58` builds a label too).
  Put both in the data rather than deriving them: `plural` and `article` fields per monster in
  `app/data/monsters.json` (100 entries). Deriving the plural is already wrong for 4 of 100.
  Deriving the article from a leading vowel happens to work for today's eight — Acolyte, Orc,
  Oil Beetle, Elf, Ochre Jelly, Ogre, Owl Bear, Amber Golem — but breaks the moment a Unicorn
  or an Umber Hulk is added, both of which take "a" despite the vowel. Data costs one field
  and is correct by construction.
- [ ] **The upkeep total collected should sit with the treasury, not under the ledger.** The
  Upkeep Day modal shows `Treasury [before] -> [after]` on one line
  (`UpkeepDayModal.vue:44-54`), while the amount actually taken in appears as a "Collected"
  cell at the bottom of the per-adventurer grid (`:88-91`). The headline number is the one
  buried. Show it as **`+X` directly beneath the original treasury value**, as first-class
  information.
  No backend work: the payload already carries `collected_cp`, and it equals
  `treasury_after_cp - treasury_before_cp`, so the figure needs no computing.
  Two things to settle while doing it: `.outcome-row` is a single horizontal line of spans, so
  a value *below* the before-figure means stacking that cell rather than adding another span;
  and the grid's totals row also carries collected XP and any unpaid amount, so decide whether
  the money cell moves out of it (leaving XP and unpaid behind) or is shown in both places.

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

### v1.1 — queued 2026-09-09
- **A morale check when the party is at half its total HP or less.** Today morale only fires
  after a *death* (`party_deaths_in_round > 0`), so six adventurers at 1 HP each with nobody
  dead never check at all. An HP-threshold check lets a party leave before the first corpse,
  which is what actually prevents a wipe rather than mitigating one.
- **"Skip to Event" should stop only at something actionable.** An auto-launching expedition
  currently halts the skip. Immediate cause: the auto-launch event is emitted with
  `type="expedition_complete"` (`app/routes/game.py:356`) — a launch announced as a completion
  — and `expedition_complete` is in `NOTABLE_EVENT_TYPES` (`app/routes/game.py:508`), which is
  the set `skip_to_event` breaks on. Give the launch its own type and the immediate bug goes.
  The broader fix is that `NOTABLE_EVENT_TYPES` conflates two different questions — *does this
  belong in the log* and *should time stop for this*. Splitting them lets recruitment, loot and
  an auto-launch be recorded without interrupting a skip, while a pending decision, the upkeep
  ledger and a death still stop the clock. **Stairs must keep stopping it regardless**: they
  always prompt the player, by standing rule. Worth checking the mislabelled type does not also
  make the frontend treat a launch as a return.

- **A routed party should not collect the treasure.** `determine_room_contents()`
  (`app/expedition.py:629`) returns `[MONSTER, TREASURE]` for two-thirds of monster rooms, and
  the encounter loop iterates that list **without reading the combat outcome at all** — so a
  party that breaks and runs still takes the hoard from the room it just fled. It also still
  banks `treasure["xp_value"]`, which leaks around the deliberate 0-XP-on-flee rule.
  **Interaction to weigh:** at the old morale of 11 this fired in ~5.5% of lethal combats and
  barely mattered. At 7 it is ~66%, so fleeing now keeps the loot, the treasure XP, and (as of
  2026-09-09) the healing. Nothing here is player-exploitable — morale is rolled, not chosen —
  but it makes a rout much cheaper than intended. Worth asking whether this belongs in v1
  alongside the morale change rather than waiting.
- **A flee raises an event.** Every time a party breaks off combat the player should see it.
  Today the outcome `"Party Fled"` is set and **nothing anywhere reads it** — no event, no
  notification, no branch. With morale at 7 this will now happen often, so it needs to be
  visible or the player will not understand why a delve went badly.

- **The in-process simulator never forgets a launch.** `app/routes/expeditions.py:40` holds one
  `DungeonSimulator` for the life of the process, and every launch appends a party list and an
  expedition record to it that nothing removes. The database is unaffected; this is Python
  memory, growing by one small dict-tree per launch. Harmless for a cohort of ten, real for a
  long-running process. A per-launch simulator removes it, but `get_expedition_results` and
  `advance_turn` (`:913`, `:1342`) still read the global by *database* expedition id, which
  the simulator does not key on, so those two legacy endpoints need retiring or rewiring first.
- **Auto-decided stairs never change the party's level.** The day-advance loop
  (`app/routes/game.py:389`, `:433`) tests for a `press_on_next` choice, but `auto_decide`
  (`app/expedition_events.py:32`) only ever returns `press_on` or `retreat`, so the
  `dungeon_level` update behind that test is dead. Stairs always prompt the player by standing
  rule, so today nothing reaches it; it matters the moment an auto-decide party is allowed to
  take stairs on its own.

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

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
      **This is a bug in its own right and does not depend on anything else** — the panel
      under-reports whatever the bonuses happen to be. Preferably shipped alongside the
      buildings-XP item below, since that changes the one effect currently visible, but either
      can land alone
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
- [ ] **Dead adventurers can be sent on further expeditions.** Confirmed 2026-09-09 in Cody's
      save: Faust Anvilstrike, Tinariel Overhill and Audild Phoenixash all died on **day 2**
      (expedition 891, a Sprite rout) and all three appear in **expedition 892 on day 35** —
      casting spells, being targeted, and Faust being slain a second time.
      **Cause:** `is_dead` is written to the database only in `_finalize_expedition`
      (`app/routes/expeditions.py:255`), which runs when the player *witnesses* the
      resolution. Expedition 891 was not resolved until roughly day 36 — which is when its
      death popup finally fired. For 33 days those three were dead in the simulation and alive
      in the database, so the launch guard at `:667` (and the auto-launch filter at `:541`)
      read `is_dead == False` and let them out again.
      **Fix, ruled 2026-09-09: apply deaths to the roster when the expedition resolves in the
      simulation, and hold only the *event* back for the player to witness.** The witnessed
      rule exists to delay display; it must never delay state. The narrower alternative —
      having launch consult the pending simulation instead of `is_dead` — was considered and
      rejected: it patches one caller and leaves the divergence for whatever reads `is_dead`
      next.
      **v1.0 blocker, scheduled for the 2026-09-12/13 weekend.** A ghost party member is not
      merely a cosmetic error: they soak attacks, deal damage, cast spells and count toward
      party size, so every fight they appear in has the wrong odds in an unknown direction.
      It also corrupts the save, wastes a player's roster, and delivers the death moment — the
      attachment moment the cohort exists to test — 33 days late attached to the wrong fight.
      **Balance data gathered before this is fixed is contaminated** and should be re-measured
      afterwards with `scripts/balance_stats.py`.
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
      The +10% is provisional, like the 10% building costs. Related to the Village legibility
      item above — this changes the one effect that panel happens to show — but the two are
      independent: the Village under-reports either way, so neither blocks the other
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

### v1.1 — queued 2026-09-09
- **A morale check when the party is at half its total HP or less.** Today morale only fires
  after a *death* (`party_deaths_in_round > 0`), so six adventurers at 1 HP each with nobody
  dead never check at all. An HP-threshold check lets a party leave before the first corpse,
  which is what actually prevents a wipe rather than mitigating one.
- **The upkeep total collected should sit with the treasury, not under the ledger.** The
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
- **Monsters need a plural form and an article.** Singular combat reads "Your party fought
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
- **Village belongs beside the roster, not below the fold.** On the Dashboard,
  `.parties-unassigned-grid` (`DashboardView.vue:537`) is a two-column `1fr 1fr` grid holding
  Parties and Unassigned Adventurers; the Village card (`:450`, with the empty-state variant at
  `:500`) sits full-width **underneath it**. Since Village is a drop target for building
  assignment, assigning an unassigned adventurer means dragging while scrolling, which HTML5
  drag handles poorly. Move Village to half width directly under Unassigned Adventurers — it
  removes the scroll and fills the blank right-hand space.
  Implementation note: making Village a fourth child of the existing grid does not achieve
  this — grid rows align across columns, so a tall Parties card would leave a gap above
  Village. Restructure as two independent column stacks instead: left holds Parties, right
  holds Unassigned Adventurers then Village. Both Village blocks move, the populated one and
  the empty state.
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
- **Adventurer rows should line up in columns.** Quality of life. The Dashboard's unassigned
  list (`DashboardView.vue:335-352`) is a flex row of inline `<span>`s, so no statistic sits at
  the same horizontal position from one adventurer to the next. The item tags are rendered
  **before** class, level, HP, XP and wealth, so a variable number of items shifts every
  statistic after them — which is why rows look aligned until someone picks something up.
  Four or more items is rare enough to accept as the degrading case, so a fixed-width item
  cell that overflows there is fine.
  Same pattern in `PartiesView.vue`, `ExpeditionLaunchView.vue` and `PartyFormationView.vue`;
  `AdventurerList.vue`, `ExpeditionList.vue`, `RecentExpeditions.vue` and `MetricsPanel.vue`
  already use real tables. Implementation note: the Dashboard rows are `draggable` with
  dragstart handlers, and dragging `<tr>` elements is awkward — CSS Grid with fixed
  `grid-template-columns` keeps the existing `<div>` structure and the drag behaviour while
  giving the same alignment. (`fix/table-alignment` holds nothing unique against `main`.)
- **Adventurer names in the expedition summary should open their sheet.** v0.9 shipped this
  for notifications and popups, but `linkAdventurerNames` (`frontend/src/utils/adventurer.ts`)
  is used in exactly one place — `SidePanel.vue`. `ExpeditionSummaryView.vue`,
  `ExpeditionLogTree.vue` and `ExpeditionEventModal.vue` link nothing. Two distinct cases:
  the **member rows** (`ExpeditionSummaryView.vue:246`) already hold member objects with ids,
  so they link directly; the **log-tree prose** ("X healed for 2 HP by Y", "Z is revived by Y")
  is built from `healed_adventurers` / `revivals` entries that carry `name` but **no id**, so
  those need either name-to-id resolution against the party roster the view already has, or
  ids added to those payloads — the same discipline the notification path uses, where only
  backend-attached names are matched so a party named after an adventurer is never mistaken
  for one. Being the fourth surface to need this, it is worth extracting the shared
  `AdventurerLink` component the v0.9 work stopped short of
- **The live expedition summary should show healing per member.** Today a member row can read
  a loss next to full health — "-4" beside "6/6 HP" — which looks like a bug because nothing
  reconciles the two numbers. It is not a bug: `_replay_member_hp`
  (`app/routes/expeditions.py:1046`) applies attack damage, then revivals, then
  `healed_adventurers`, so the *final* HP is right; the damage figure and the HP bar are simply
  computed from different halves of the story with the healing invisible between them.
  Surfacing, not new mechanics: the replay already consumes per-member healing and revivals and
  just folds them into one number instead of returning them. Have it return per-member healing
  and revival totals, and render them on the member row
  (`ExpeditionSummaryView.vue:246`, `ExpeditionEventModal.vue`) so the arithmetic reads: took
  4, healed 4, ended 6/6. Pairs naturally with the in-round healing display above
- **The round log should replay one ordered event list.** The sim records a round as separate
  buckets — `attacks`, `spell_casts`, `cleric_turns` — and builds `revivals` and
  `healed_adventurers` *after* the round loop with no round number at all. The renderer
  (`ExpeditionLogTree.vue:185-208`) emits those buckets in a fixed order, so the log's
  chronology is a reconstruction, and it is wrong in three known ways:
  · on a **monsters-first** round the spell renders *before* the monster attacks that actually
  preceded it (observed 2026-09-09: "Round 1 (monsters first)" listing Sleep above sixteen Ogre
  attacks) · **Cleric turn undead** renders after the spell, but resolves before everything,
  since it happens regardless of initiative · **heals and revivals** hang off the end of the
  combat rather than appearing where they occurred.
  **The simulation is correct in every one of these — only the log misrepresents it.**
  Fix: have `resolve_combat_rounds` append to a single ordered `events` list per round and have
  the renderer play it back, with post-combat recovery tagged to the round it belongs to. That
  closes all three at once and stops the next addition from creating a fourth. It also removes
  the renderer's need to infer which side an attack came from by looking the attacker's name up
  in `pcNames` (`ExpeditionLogTree.vue:57`).

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
- **Armor should reduce damage or raise Armor Class**, not add temporary hit points. Balance
  change, deferred so the cohort's death data lands first. See the armor item in v0.9.1.

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

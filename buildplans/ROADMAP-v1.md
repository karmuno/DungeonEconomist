# VentureKeep Roadmap — v0.7 to v1.0

Post-v0.6.1 release plan. Each version groups 3 workstreams from the v1 scope.

---

## v0.7 — The Hardened Adventurer Release

Security for real users and class identity that makes adventurers feel distinct.

### Auth Hardening
- Rate limiting on login/register
- Password strength requirements
- Token refresh / expiry improvements
- CORS lockdown for production origins
- Session invalidation on password change

### Simplified Class Abilities
- **Cleric**: heal (restore HP to party members mid-expedition)
- **Magic-User**: cast (area damage or utility effect)
- NOT full spell slots — one signature ability per class, usable per expedition
- Class abilities should influence expedition event outcomes

### Resurrection System
- Temple building (or Shrine upgrade path) enables resurrection
- Requires high-level Cleric assigned to the building
- Gold cost scaling with adventurer level
- Moves adventurer from Graveyard back to Recovering
- Comes back at reduced HP/XP or with a penalty

---

## v0.8 — The Dungeon Release

The dungeon gets deeper, the numbers get real, and there's more to find.

### Auto-Delve Completion
- Verify all auto-delve fields are fully wired end-to-end
- Auto-delve respects party readiness (healed, full, etc.)
- Edge cases: what happens when party members die mid-auto-delve?

### Game Balance Pass
- Death rate tuning by dungeon level (playtest-informed)
- Loot vs. risk curve across all 6 levels
- Upkeep cost scaling — is 1cp/XP still right?
- Building bonus tuning (healing rate, combat strength, item discovery)
- Magic item drop rate vs. Library bonus
- Class ability power levels

### More Content
- More monsters beyond the initial 12 (deeper levels especially)
- New buildings: Wizard's Tower, Fighter Stronghold
- More magic item variety
- Non-combat expedition events (NPCs, puzzles, environmental)
- Dungeon flavor text / room descriptions

---

## v0.9 — The Polish Release

Goal: A new player can understand the game, enter the core loop, and become invested in what happens to their adventurers.

This is your UX release.

### Core UX Overhaul
- Adventurer detail modal as a character sheet that emphasizes stats, progression, history, and items
- Expedition progress visualization
- Village/building UI improvements
- Responsive layout for mobile if it fits without derailing the release

### Onboarding & Direction
First-login flow guiding players through:
- Recruitment
- Party formation
- First expedition
- Contextual hints
- "What to do next" suggestions on the dashboard
- Help/info tooltips on important mechanics

### Error Handling & Edge Cases
- Graceful handling of known failure modes
- API error responses with actionable messages
- Frontend error boundaries and retry logic where appropriate
Handle:
- Empty parties
- Bankrupt Keeps
- All-dead rosters
- Audit critical expedition events and state transitions for silent failure

That last one should probably be an explicit lesson from the stairs problem:

> Meaningful game events must either resolve correctly or fail visibly.

Then we begin the march through the v0.9.x releases.

---

## v0.9.1 — The Observable Keep

Goal: Understand what players do and what the game does when they do it.

This is where you add instrumentation and better operational visibility.

### Player Journey
- Account created
- Adventurer recruited
- Party formed
- Expedition started
- Expedition completed
- Building purchased/upgraded
- Return session
- Repeat expedition

### Attachment Events
- Adventurer levels up
- Adventurer reaches level 2
- Adventurer dies
- High-level adventurer dies
- Party wipe
- Player continues after a meaningful death

### Operational Visibility
- Server-side exception logging
- Visibility into failed API calls
- Visibility into critical UI failures

The objective:

> Can we see whether players reach the attachment loop, and can we see when the machine breaks?

---

## v0.9.2 — The Survivable Keep

Goal: VentureKeep can survive technical failure without destroying player worlds.

### Production Database Confidence
- Integration tests against Postgres

### Backup & Recovery
- Database backup procedure
- Automated backups if practical
- Documented recovery procedure
- Successful recovery test

The acceptance criterion is:

> We have intentionally tested restoring VentureKeep from a backup.

### Deployment
- Lightweight deployment documentation
- Enough information for Future Cody to safely deploy, recover, and troubleshoot the game

---

## v0.9.3 — The Public Keep

Goal: VentureKeep can safely support the first deliberately invited strangers.

### Security
- Dependency review
- Authentication-flow review
- Input validation review
- Fix obvious production vulnerabilities

### Load & Concurrent Users
- Test concurrent-user behavior
- Determine approximately what the VPS can comfortably support
- Identify obvious bottlenecks
- Establish a reasonable initial player cohort

### Performance
- Fix obvious slow queries or major frontend bottlenecks discovered during testing

### Browser Sanity
- Verify that the game works in the browsers you reasonably expect strangers to use

---

## v0.9.4 — The Final Delve

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

---

## v1.0 — Let Them Delve

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
- Invite a deliberately small initial cohort
- Monitor stability
- Observe the player journey
- Collect feedback
- Watch for evidence of player attachment
- Track return behavior

### First Economic Experiment

Add the simplest possible voluntary support mechanism.

Something like:

> Enjoying VentureKeep? Support its development.

The goal is not to optimize conversion.

The goal is to discover whether the flywheel can complete its first economic cycle:

Great Machine → Passionate Player → Value → Resources → Better Machine

---

## The Overall Progression

| Version | Question it answers |
| :--- | :--- |
| **v0.9** | Can a new player understand and enjoy VentureKeep? |
| **v0.9.1** | Can we understand what players do? |
| **v0.9.2** | Can we survive failure without losing player worlds? |
| **v0.9.3** | Can we safely invite strangers? |
| **v0.9.4** | Does the complete experience hold together? |
| **v1.0** | What happens when real people play? |

Make it understandable → make it observable → make it survivable → make it public → verify the whole experience → let them delve.

---

## Explicitly Deferred to Post-V1
- Full spell management system
- Parlay / monster reaction table
- Dungeon procedural generation / node navigation
- Followers / henchmen
- Payment integration / legal
- Analytics / telemetry

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
- **Fighter**: cleave (bonus attack on kill)
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

The game works; now make it feel good for new players.

### Core UX Overhaul
- Adventurer detail modal as a real character sheet (stats, history, items)
- Expedition progress visualization
- Village/building UI improvements
- Responsive layout for mobile

### Error Handling & Edge Cases
- Graceful handling of all failure modes
- API error responses with actionable messages
- Frontend error boundaries and retry logic
- Edge cases: empty parties, bankrupt keeps, all-dead rosters

### Onboarding / Tutorial
- First-login flow guiding players through recruitment → party → expedition
- Contextual hints (already partially in place)
- "What to do next" suggestions on dashboard
- Help/info tooltips on game mechanics

---

## v0.9 → v1.0 — The Hardening Pass

Feature-frozen. No new gameplay. Only stability, correctness, and confidence.

- Integration tests against Postgres (v1 blocker — SQLite test suite is not sufficient)
- Load testing / concurrent user behavior
- Database backup and recovery procedures
- Deployment documentation
- Security audit (dependencies, auth flows, input validation)
- Performance profiling (slow queries, frontend bundle size)
- Cross-browser testing
- Final playtest for game-breaking edge cases

---

## Explicitly Deferred to Post-V1
- Full spell management system
- Parlay / monster reaction table
- Dungeon procedural generation / node navigation
- Followers / henchmen
- Payment integration / legal
- Analytics / telemetry

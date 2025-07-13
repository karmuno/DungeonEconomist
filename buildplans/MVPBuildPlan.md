# MVP Build Plan

## Next Steps
1. Balance risk vs. reward for different dungeon difficulties
2. Expeditions need to auto-complete when they are "Ready to Return"
3. Write unit tests for simulation engine
4. Create integration tests for full expedition flow
5. Test and balance economy

## Complete Task List

### Core Setup & Models (Completed)
- [x] Set up project skeleton and repo
- [x] Define adventurer classes and models
- [x] Create SQLite schema
- [x] Implement basic API structure with FastAPI
- [x] Build seed script for adventurer pool

### Simulation Engine (Completed)
- [x] Implement expedition engine in simulator.py
- [x] Create encounter roll system
- [x] Implement combat outcome calculation
- [x] Design treasure and XP distribution logic
- [x] Add expedition logging functionality
- [x] Build expedition results endpoint

### Frontend (Completed)
- [x] Create HTMX-based templates for viewing adventurers
- [x] Implement party formation interface
- [x] Build expedition launch and management screens
- [x] Design expedition log viewer

### Party Management
- [x] Create API endpoint to add adventurers to parties
- [x] Create API endpoint to remove adventurers from parties
- [x] Implement party expedition status tracking
- [x] Add party equipment/loadout handling

### Character Progression
- [x] Implement XP tracking and storage
- [x] Create level-up logic based on XP thresholds
- [x] Add HP improvement on level up
- [x] Implement class-specific progression benefits

### Frontend/UI
- [x] Create HTMX-based templates for viewing adventurers
- [x] Implement party formation interface
- [x] Build expedition launch and management screens
- [x] Design expedition log viewer
- [ ] Add Tailwind styling for clean retro black/white aesthetic

### Economy & Balance
- [x] Implement gold/treasure distribution
- [x] Implement treasury system with loot split (70% adventurers, 30% treasury)
- [x] Create Player model with treasury and total_score fields
- [x] Add treasury counter to UI for tracking player score
- [x] Add healing/recovery mechanics
- [x] Create upkeep costs every 30 days equal to 1% of character's XP
- [ ] Balance risk vs. reward for different dungeon difficulties

### Automation
- [x] Expeditions need to auto-complete when they are "Ready to Return"
- [x] If "Advance" causes the day to pass a multiple of 30, trigger everybody's upkeep costs

### Testing & Refinement
- [ ] Write unit tests for simulation engine
- [ ] Create integration tests for full expedition flow
- [ ] Test and balance economy
- [ ] Performance optimization for large parties/expeditions

### Stretch Goals
- [ ] Multiple interconnected dungeon nodes
- [ ] Character death and permadeath mechanics
- [ ] Town infrastructure assignments
- [ ] More advanced equipment and inventory management
# MVP Build Plan

## Next Steps
1. Add treasury counter to UI for score tracking
2. Create healing/recovery mechanics
3. Implement upkeep costs between expeditions

## Completed Tasks
1. ~~Implement treasury system with loot split (70/30)~~ ✅
2. ~~Create Player model with treasury tracking~~ ✅
3. ~~Implement gold/treasure distribution~~ ✅

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
- [ ] Create HTMX-based templates for viewing adventurers
- [ ] Implement party formation interface
- [ ] Build expedition launch and management screens
- [ ] Design expedition log viewer
- [ ] Add Tailwind styling for clean black/white aesthetic

### Economy & Balance
- [x] Implement gold/treasure distribution
- [x] Implement treasury system with loot split (70% adventurers, 30% treasury)
- [x] Create Player model with treasury and total_score fields
- [ ] Add treasury counter to UI for tracking player score
- [ ] Add healing/recovery mechanics
- [ ] Create upkeep costs between expeditions
- [ ] Balance risk vs. reward for different dungeon difficulties

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
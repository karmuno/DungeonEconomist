# MVP Build Plan

## Next Steps
1. Add party equipment/loadout handling
2. Implement XP tracking and level-up system
3. Create healing/recovery mechanics

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
- [ ] Add party equipment/loadout handling

### Character Progression
- [ ] Implement XP tracking and storage
- [ ] Create level-up logic based on XP thresholds
- [ ] Add HP improvement on level up
- [ ] Implement class-specific progression benefits

### Frontend/UI
- [ ] Create HTMX-based templates for viewing adventurers
- [ ] Implement party formation interface
- [ ] Build expedition launch and management screens
- [ ] Design expedition log viewer
- [ ] Add Tailwind styling for clean black/white aesthetic

### Economy & Balance
- [ ] Implement gold/treasure distribution
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
- [ ] Equipment and inventory management
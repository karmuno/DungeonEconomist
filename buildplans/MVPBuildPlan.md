# MVP Build Plan

## Next Steps
1. Complete simulator.py with basic expedition and encounter logic. Import what you need from expedition.py.
2. Create API endpoints for party management (add/remove adventurers)
3. Implement frontend templates with HTMX for basic interaction

## Complete Task List

### Core Setup & Models (Completed)
- [x] Set up project skeleton and repo
- [x] Define adventurer classes and models
- [x] Create SQLite schema
- [x] Implement basic API structure with FastAPI
- [x] Build seed script for adventurer pool

### Simulation Engine
- [ ] Implement expedition engine in simulator.py
- [ ] Create encounter roll system
- [ ] Implement combat outcome calculation
- [ ] Design treasure and XP distribution logic
- [ ] Add expedition logging functionality
- [ ] Build expedition results endpoint

### Party Management
- [ ] Create API endpoint to add adventurers to parties
- [ ] Create API endpoint to remove adventurers from parties
- [ ] Implement party expedition status tracking
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
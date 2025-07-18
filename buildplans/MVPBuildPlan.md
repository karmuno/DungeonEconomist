# MVP Build Plan

## Next Steps
1. Set up Flask backend with basic API endpoints and OpenAPI documentation.
2. Set up Vue.js frontend to consume backend APIs.
3. Implement core game logic in the Flask backend.
4. Integrate frontend with backend API calls.
5. Containerize Flask application for Google Cloud Run deployment.

## Complete Task List

### Core Setup & Models (Backend)
- [x] Set up Flask project skeleton.
- [ ] Define SQLAlchemy models for adventurers, parties, etc.
- [ ] Create SQLite schema.
- [ ] Implement basic Flask API structure with `flask-openapi3`.
- [ ] Build seed script for adventurer pool.
- [ ] Create Dockerfile for Flask application.

### Simulation Engine (Backend)
- [ ] Implement expedition engine in `backend/services.py`.
- [ ] Create encounter roll system.
- [ ] Implement combat outcome calculation.
- [ ] Design treasure and XP distribution logic.
- [ ] Add expedition logging functionality.
- [ ] Build expedition results API endpoint.

### Frontend (Vue.js)
- [ ] Set up Vue.js project using Vue CLI.
- [ ] Create Vue components for viewing adventurers.
- [ ] Implement party formation interface.
- [ ] Build expedition launch and management screens.
- [ ] Design expedition log viewer.
- [ ] Implement API calls to Flask backend.

### Party Management (Backend & Frontend)
- [ ] Create API endpoint to add adventurers to parties.
- [ ] Create API endpoint to remove adventurers from parties.
- [ ] Implement party expedition status tracking.
- [ ] Add party equipment/loadout handling.

### Character Progression (Backend)
- [ ] Implement XP tracking and storage.
- [ ] Create level-up logic based on XP thresholds.
- [ ] Add HP improvement on level up.
- [ ] Implement class-specific progression benefits.

### Economy & Balance (Backend)
- [ ] Implement gold/treasure distribution.
- [ ] Implement treasury system with loot split (70% adventurers, 30% treasury).
- [ ] Create Player model with treasury and total_score fields.
- [ ] Add healing/recovery mechanics.
- [ ] Create upkeep costs every 30 days equal to 1% of character's XP.
- [ ] Balance risk vs. reward for different dungeon difficulties.

### Automation (Backend)
- [ ] Expeditions need to auto-complete when they are "Ready to Return".
- [ ] If "Advance" causes the day to pass a multiple of 30, trigger everybody's upkeep costs.

### Testing & Refinement
- [ ] Write unit tests for Flask backend services.
- [ ] Create integration tests for full expedition flow.
- [ ] Write unit/integration tests for Vue.js frontend.
- [ ] Test and balance economy.
- [ ] Performance optimization for large parties/expeditions.

### Deployment (Google Cloud Run)
- [ ] Deploy Flask backend to Cloud Run.
- [ ] Deploy Vue.js frontend (e.g., Cloud Storage + CDN or separate Cloud Run service).
- [ ] (Optional) Configure API Gateway.

### Stretch Goals
- [ ] Multiple interconnected dungeon nodes.
- [ ] Character death and permadeath mechanics.
- [ ] Town infrastructure assignments.
- [ ] More advanced equipment and inventory management.
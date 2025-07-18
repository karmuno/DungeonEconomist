🛠️ Build Plan: Venturekeep Prototype
🎯 Goal
Create a functioning prototype that simulates:
A small adventurer pool


Basic party creation


Simulated dungeon expeditions with outcomes


XP/level-up mechanics


Minimal UI to manage/view everything



⚙️ Tech Stack
Area
Tool
Backend
Python (Flask), OpenAPI
Simulation/Logic
Pure Python, possibly NumPy for dice/statistics
Frontend
Vue.js
Styling/UI
Tailwind CSS (quick and clean 1-bit aesthetic)
Data Storage
SQLite (lightweight, easy to reset/test)
Deployment
Google Cloud Run (for simple cloud hosting)
Version Control
Git + GitHub
Optional Extras
Faker (for random names), Markdown for logs


🧱 Core Features in Prototype
Feature
Description
Adventurer Pool
Hardcoded or stored in SQLite; 6–10 pregen characters
Party Management
Basic UI to add/remove adventurers from a party
Dungeon Simulation
Simulate 1–3 dungeon nodes with random encounters
Expedition Results
Text log of the expedition outcome (success/failure, loot, XP, injuries)
Character Advancement
Simple XP → level-up, with class-based progression
Treasury System
Monthly gold collection with loot split (70% to adventurers, 30% to treasury)
Final Score
Track total gold accumulated in treasury as the player's final score
UI
Minimal Vue.js components with API calls to Flask backend


🗂️ Project Structure
Venturekeep/
├── backend/
│   ├── app.py         # Flask entrypoint
│   ├── models.py       # Adventurer, Party, DungeonNode, Player, etc.
│   ├── services.py    # Core expedition logic, calculate_loot_split()
│   └── Dockerfile      # For Cloud Run deployment
├── frontend/
│   ├── src/            # Vue.js source code
│   ├── public/         # Static assets
│   └── package.json    # Frontend dependencies
├── data/
│   └── db.sqlite       # Initial DB
├── tests/
│   ├── backend/        # Backend unit tests
│   └── frontend/       # Frontend unit tests
├── requirements.txt    # Backend Python dependencies
└── README.md


🔄 Development Milestones (2–4 weeks)
Week 1: Core Setup & Backend API
Set up Flask project skeleton with OpenAPI.
Build adventurer, party, and dungeon models.
Create hardcoded adventurer pool.
Scaffold SQLite schema and seed script.
Implement basic API endpoints for CRUD operations.

Week 2: Dungeon Simulation Engine & Backend Logic
Implement a basic expedition engine with:
Encounter rolls
Combat outcomes (abstracted)
Treasure/XP calculation
Write a readable expedition log output.

Week 3: Frontend UI & Integration
Set up Vue.js project.
Create Vue components for:
Viewing adventurers
Forming parties
Launching expeditions
Viewing logs
Integrate Vue.js with Flask API calls.

Week 4: Progression & Polish
Implement XP → Level up logic.
Track expedition history.
Add healing/upkeep costs between turns.
Implement treasury system with loot split (70/30).
Add treasury counter to UI.
Bug fixes, basic testing.
Containerize Flask app and prepare for Cloud Run deployment.


🧪 Stretch Goals (If Time Allows)
Multiple dungeon nodes


Party loadout/equipment handling


Character death and permadeath log


Assign characters to town infrastructure



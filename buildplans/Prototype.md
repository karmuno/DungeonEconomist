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
Python (Flask or FastAPI)
Simulation/Logic
Pure Python, possibly NumPy for dice/statistics
Frontend
HTMX + Alpine.js (for interactivity without full frontend framework)
Styling/UI
Tailwind CSS (quick and clean 1-bit aesthetic)
Data Storage
SQLite (lightweight, easy to reset/test)
Deployment
Render.com or Fly.io (for simple cloud hosting)
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
UI
Minimal HTML with HTMX interactions (no page reloads)


🗂️ Project Structure
Venturekeep/
├── app/
│   ├── __init__.py
│   ├── main.py         # Flask/FastAPI entrypoint
│   ├── models.py       # Adventurer, Party, DungeonNode, etc.
│   ├── simulator.py    # Core expedition logic
│   └── templates/
│       └── *.html      # HTMX templates
├── static/
│   ├── styles.css      # Tailwind CSS
├── data/
│   └── db.sqlite       # Initial DB
├── tests/
│   └── test_sim.py     # Unit tests for dungeon sim
├── requirements.txt
└── README.md


🔄 Development Milestones (2–4 weeks)
Week 1: Core Setup & Models
Set up project skeleton and repo


Build adventurer, party, and dungeon models


Create hardcoded adventurer pool


Scaffold SQLite schema and seed script


Week 2: Dungeon Simulation Engine
Implement a basic expedition engine with:


Encounter rolls


Combat outcomes (abstracted)


Treasure/XP calculation


Write a readable expedition log output


Week 3: UI & Interactions
HTMX-based UI for:


Viewing adventurers


Forming parties


Launching expeditions


Viewing logs


Add Tailwind styling for a clean black/white look


Week 4: Progression & Polish
Implement XP → Level up logic


Track expedition history


Add healing/upkeep costs between turns


Bug fixes, basic testing



🧪 Stretch Goals (If Time Allows)
Multiple dungeon nodes


Party loadout/equipment handling


Character death and permadeath log


Assign characters to town infrastructure



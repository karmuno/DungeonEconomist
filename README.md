# Venturekeep

A retro RPG party management simulation. Manage a pool of adventurers, form parties, send them on dungeon expeditions, and run an economy of gold, XP, and upkeep.

Built with **FastAPI**, **SQLAlchemy**, **Vue 3**, and **TypeScript**. Inspired by classic tabletop RPG resource management.

## Features

- **Adventurer Management** — Create and manage adventurers across 6 classic classes (Fighter, Cleric, Magic-User, Elf, Dwarf, Hobbit). Track XP, HP, gold, and equipment.
- **Party System** — Form parties of 2-9 adventurers with shared funds and supply inventories.
- **Dungeon Expeditions** — Send parties into dungeons with scaling difficulty (levels 1-6). Combat, traps, treasure, and special items are resolved through a turn-based simulation engine.
- **Character Progression** — 10-level progression system with class-specific HP gains, bonuses, and XP thresholds following classic RPG curves.
- **Economy** — Loot splits (70% adventurers / 30% treasury), upkeep costs every 30 game days, bankruptcy mechanics, and equipment purchasing.
- **Game Time** — Advance days to trigger expedition returns, upkeep cycles, and healing.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
git clone https://github.com/Cody-Jane-Stahl/DungeonEconomist.git
cd DungeonEconomist

# Backend: create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Frontend: install dependencies
cd frontend
npm install
cd ..
```

### Development

Run the backend and frontend dev servers in separate terminals:

```bash
# Terminal 1: Backend API (port 8000)
uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend dev server (port 5173)
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) for the app. The Vite dev server proxies all API requests to the backend.

API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Production Build

```bash
cd frontend
npm run build
cd ..

# Serve everything from FastAPI
uvicorn app.main:app --port 8000
```

The FastAPI server serves the Vue build from `frontend/dist/` automatically. Open [http://localhost:8000](http://localhost:8000).

### Seeding Data

```bash
python -m app.seed_adventurers   # Creates 20 starting adventurers
python -m app.seed_equipment     # Creates equipment and supply catalogs
```

### Resetting the Database

The game uses a SQLite database at `./data/db.sqlite`. To start fresh:

```bash
rm -f data/db.sqlite    # or delete the file manually
# Restart the server — tables will be recreated
```

## Project Structure

```
app/
├── main.py              # FastAPI app setup + Vue SPA serving
├── database.py          # Database engine, session, and dependency
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic request/response schemas
├── simulator.py         # Dungeon simulation engine
├── expedition.py        # Expedition mechanics and combat resolution
├── progression.py       # XP thresholds and level-up system
├── seed_adventurers.py  # Initial adventurer pool (20 characters)
├── seed_equipment.py    # Equipment and supply seed data
├── routes/
│   ├── adventurers.py   # Adventurer CRUD + level-up + equipment
│   ├── players.py       # Player CRUD
│   ├── parties.py       # Party management, members, supplies, funds
│   ├── equipment.py     # Equipment catalog endpoints
│   ├── expeditions.py   # Expedition launch, results, and turn advancement
│   └── game.py          # Game time, upkeep, and dashboard stats

frontend/                # Vue 3 + Vite + TypeScript SPA
├── src/
│   ├── api/             # Typed API client modules
│   ├── assets/          # CSS (retro terminal theme)
│   ├── components/      # Vue components (layout, shared, domain)
│   ├── composables/     # Reusable composition functions
│   ├── router/          # Vue Router configuration
│   ├── stores/          # Pinia state management
│   ├── types/           # TypeScript interfaces
│   └── views/           # Page-level view components

tests/                   # Pytest test suite
buildplans/              # Design documents and roadmap
```

## Running Tests

```bash
pytest
```

## Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite
- **Frontend**: [Vue 3](https://vuejs.org/) + [Vite](https://vite.dev/) + [TypeScript](https://www.typescriptlang.org/) + [Pinia](https://pinia.vuejs.org/) + [Vue Router](https://router.vuejs.org/)
- **Testing**: [pytest](https://pytest.org/) + [httpx](https://www.python-httpx.org/)

## License

[MIT](LICENSE)

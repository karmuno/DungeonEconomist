# Venturekeep

A retro RPG party management simulation. Manage a pool of adventurers, form parties, send them on dungeon expeditions, and run an economy of gold, XP, and upkeep.

Built with **FastAPI**, **SQLAlchemy**, **Vue 3**, and **TypeScript**. Inspired by classic tabletop RPG resource management.

**[Try the live demo](https://venturekeep.stahlsystems.com/)** — This is a highly experimental project. Data may be reset at any time.

## Features

- **Adventurer Management** — Manage adventurers across 6 classic classes (Fighter, Cleric, Magic-User, Elf, Dwarf, Halfling). Track XP, HP, gold, and magic items.
- **Village Buildings** — Construct and upgrade buildings like the **Temple**, **Smithy**, **Library**, and **Training Grounds**. Assign adventurers to buildings to unlock passive bonuses, craft magic items, and boost recruitment.
- **Party System** — Form parties of 1-6 adventurers.
- **Dungeon Expeditions** — Send parties into dungeons with scaling difficulty (levels 1-6). Combat, traps, treasure, and special items are resolved through a turn-based simulation engine.
- **Auto-Delve System** — Configure parties to automatically re-enter dungeons when healed or fully recovered, with customizable auto-decision settings for expedition events.
- **Character Progression** — 10-level progression system with class-specific HP rolls, bonuses, and XP thresholds following classic RPG curves.
- **Economy** — Loot splits, monthly upkeep costs (1cp per XP), building construction, and bankruptcy mechanics.
- **Game Time** — Advance days to trigger recruitment, expedition returns, upkeep cycles, and healing.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
git clone https://github.com/karmuno/DungeonEconomist.git
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

### Docker (Postgres)

For local development with Postgres:

```bash
# Start only Postgres (run app natively with hot-reload)
docker compose up db
cp .env.example .env          # DATABASE_URL points to local Postgres
source .env && alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Or start everything in Docker (no hot-reload)
docker compose up --build
```

Open [http://localhost:8000](http://localhost:8000). Data persists in a Docker volume across restarts.

### Production Build

```bash
cd frontend
npm run build
cd ..

# Serve everything from FastAPI
uvicorn app.main:app --port 8000
```

The FastAPI server serves the Vue build from `frontend/dist/` automatically. Open [http://localhost:8000](http://localhost:8000).

### Starting a Game

Venturekeep uses a multi-keep system. Once registered, you can create a new **Keep**. Every new Keep starts with:
- A randomly generated dungeon.
- Six starting adventurers (one of each class).
- 0 gold in the treasury.

Use the **Advance Day** button to trigger recruitment and progress time.

### Resetting the Database

The game uses a SQLite database at `./data/db.sqlite` by default. To start fresh:

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
├── buildings.py         # Building configuration and bonuses
├── class_config.py      # Per-class HP, THAC0, and XP tables
├── routes/
│   ├── auth.py          # Authentication and account management
│   ├── keeps.py         # Keep CRUD and initialization
│   ├── buildings.py     # Building purchase, upgrade, and assignment
│   ├── adventurers.py   # Adventurer CRUD + level-up
│   ├── parties.py       # Party management, members, and auto-delve settings
│   ├── expeditions.py   # Expedition launch, results, and event resolution
│   ├── game.py          # Game time, recruitment, upkeep, and stats
│   └── admin.py         # Admin console commands (gp, xp, items)

frontend/                # Vue 3 + Vite + TypeScript SPA
├── src/
│   ├── api/             # Typed API client modules
│   ├── assets/          # CSS and global styles
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

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite/Postgres
- **Frontend**: [Vue 3](https://vuejs.org/) + [Vite](https://vite.dev/) + [TypeScript](https://www.typescriptlang.org/) + [Pinia](https://pinia.vuejs.org/) + [Vue Router](https://router.vuejs.org/)
- **Testing**: [pytest](https://pytest.org/) + [httpx](https://www.python-httpx.org/)

## License

[MIT](LICENSE)

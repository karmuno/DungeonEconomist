# Venturekeep

A D&D-inspired party management simulation game. Manage a pool of adventurers, form parties, send them on dungeon expeditions, and run an economy of gold, XP, and upkeep.

Built with **FastAPI**, **SQLAlchemy**, **HTMX**, and **Jinja2** templates. Inspired by OD&D/AD&D resource management.

## Features

- **Adventurer Management** — Create and manage adventurers across 6 classic classes (Fighter, Cleric, Magic-User, Elf, Dwarf, Hobbit). Track XP, HP, gold, and equipment.
- **Party System** — Form parties of 2-9 adventurers with shared funds and supply inventories.
- **Dungeon Expeditions** — Send parties into dungeons with scaling difficulty (levels 1-6). Combat, traps, treasure, and special items are resolved through a turn-based simulation engine.
- **Character Progression** — 10-level progression system with class-specific HP gains, bonuses, and XP thresholds following classic D&D curves.
- **Economy** — Loot splits (70% adventurers / 30% treasury), upkeep costs every 30 game days, bankruptcy mechanics, and equipment purchasing.
- **Game Time** — Advance days to trigger expedition returns, upkeep cycles, and healing.

## Getting Started

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
git clone https://github.com/Cody-Jane-Stahl/DungeonEconomist.git
cd DungeonEconomist

# Create virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt
```

### Running

```bash
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the web UI, or [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive API docs.

### Resetting the Database

The game uses a SQLite database at `./data/db.sqlite`. To start fresh:

```bash
rm -f data/db.sqlite    # or delete the file manually
# Restart the server — tables and seed data will be recreated
```

## Project Structure

```
app/
├── main.py              # FastAPI app setup and home page route
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
│   └── game.py          # Game time advancement and upkeep
└── templates/           # Jinja2 + HTMX templates

static/                  # CSS and images
tests/                   # Pytest test suite
buildplans/              # Design documents and roadmap
```

## Running Tests

```bash
pytest
```

## Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite
- **Frontend**: [HTMX](https://htmx.org/) + [Jinja2](https://jinja.palletsprojects.com/) templates
- **Testing**: [pytest](https://pytest.org/) + [httpx](https://www.python-httpx.org/)

## License

[MIT](LICENSE)

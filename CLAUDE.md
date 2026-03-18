# CLAUDE.md — Venturekeep

Retro RPG party management sim: FastAPI + SQLAlchemy + SQLite backend, Vue 3 + TypeScript + Pinia frontend.

## Quick Reference

- See [README.md](README.md) for full architecture, project structure, and setup instructions.
- See [buildplans/](buildplans/) for design docs and roadmap.

## Build & Run

```bash
# Backend (port 8000)
python -m app.main

# Frontend dev server (port 5173)
cd frontend && npm run dev

# Seed data
python -m app.seed_adventurers
python -m app.seed_equipment
```

## Test & Lint

```bash
# Tests
pytest tests/
pytest tests/test_sim.py::test_name    # single test

# Lint (Python)
ruff check .
ruff check --fix .

# Lint (Frontend)
cd frontend && npx eslint .

# Type check
mypy .
cd frontend && npx vue-tsc --noEmit
```

## Critical Constraints

- **Package management**: Use `uv`, not pip.
- **Schema changes**: Always use Alembic migrations (`alembic revision --autogenerate`). Never delete the database to migrate.
- **Database**: SQLite at `./data/db.sqlite`. Use SQLAlchemy sessions with FastAPI dependency injection.
- **Virtual environment**: Always activate `.venv` before running Python commands.

## Git Workflow

- **Session start**: Pull latest from `main` before starting work (`git pull origin main`).
- **During work**: Commit and push at every natural stopping point — after completing a significant task or a batch of small related tasks. Never let uncommitted work accumulate.
- **Periodic pull**: Re-pull from `main` every ~10-15 tasks to stay current.
- **Branches**: Always work on feature branches. Create PRs for merge.

## Scoped Rules

Additional conventions are in `.claude/rules/`:
- `python-style.md` — Python code style (applies to `app/**`, `tests/**`)
- `frontend-style.md` — Vue/TypeScript conventions (applies to `frontend/**`)
- `testing.md` — Testing conventions

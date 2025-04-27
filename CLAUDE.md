# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure
Venturekeep - A D&D Party Management Simulation using FastAPI, SQLAlchemy, and SQLite

## Build Commands
- Run server: `python -m app.main`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/test_sim.py::test_name`
- Seed adventurers: `python -m app.seed_adventurers` 
- Seed equipment: `python -m app.seed_equipment`
- Lint code: `flake8`
- Type check: `mypy .`

## Code Style Guidelines
- Imports: Standard library first, then third-party, then local modules
- Formatting: Follow PEP 8 (4 spaces for indentation)
- Types: Use type hints for function parameters and return values
- Models: SQLAlchemy models in models.py with snake_case naming
- Schemas: Pydantic models in schemas.py with PascalCase naming
- Error Handling: Use FastAPI's HTTPException for API errors
- Database: Use SQLAlchemy Session with dependency injection
- Enums: Use Python's enum module for enumerations
- Docstrings: Use """ """ style docstrings for classes and functions
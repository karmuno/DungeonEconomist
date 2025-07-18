# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure
DungeonEconomist - A D&D Party Management Simulation using Flask, SQLAlchemy, Vue.js, and OpenAPI.

## Build Commands

### Backend (Flask)
- Run server: `cd backend && flask run`
- Run tests: `cd backend && pytest tests/`
- Run single test: `cd backend && pytest tests/test_some_module.py::test_name`
- Lint code: `cd backend && ruff check .`
- Format code: `cd backend && black .`

### Frontend (Vue.js)
- Run development server: `cd frontend && npm run serve`
- Build for production: `cd frontend && npm run build`
- Run tests: `cd frontend && npm test`
- Lint code: `cd frontend && npm run lint`

## Code Style Guidelines

### Python (Backend)
- Imports: Standard library first, then third-party, then local modules
- Formatting: Follow PEP 8 (4 spaces for indentation)
- Types: Use type hints for function parameters and return values
- Models: SQLAlchemy models in `backend/models.py` with snake_case naming
- Schemas: Pydantic/Marshmallow models in `backend/schemas.py` with PascalCase naming
- Error Handling: Use Flask's error handling mechanisms and appropriate HTTP status codes
- Database: Use SQLAlchemy Session with dependency injection
- Enums: Use Python's enum module for enumerations
- Docstrings: Use `""" """` style docstrings for classes and functions
- OpenAPI: Ensure API endpoints are documented with OpenAPI specifications.

### JavaScript/Vue (Frontend)
- Follow Vue.js style guide.
- Use ESLint and Prettier for linting and formatting.
- Component structure: Organize components logically.
- State Management: (To be determined, e.g., Pinia or Vuex)

## Development Environment
- Use the virtual environment for backend development.
- Node.js and npm/yarn for frontend development.

## Memories
- Read the README for overall project setup.
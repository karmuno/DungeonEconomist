# DungeonEconomist - AI Agent Guidelines

This document provides guidelines and context for AI agents interacting with the DungeonEconomist codebase.

## 1. Project Overview

DungeonEconomist is a FastAPI application simulating a D&D party management game. It allows users to create players, parties, adventurers, manage equipment and supplies, and send parties on expeditions. The frontend is rendered using Jinja2 templates with HTMX for dynamic interactions.

## 2. Technology Stack

*   **Backend:** Python 3.10+, FastAPI, SQLAlchemy (ORM)
*   **Database:** SQLite (`data/db.sqlite`)
*   **Frontend:** Jinja2 (templating engine), HTMX (for dynamic UI updates), Tailwind CSS (implied by class names in templates)
*   **Web Server:** Uvicorn
*   **Testing:** Pytest

## 3. Directory Structure

*   `app/`: Contains the core application logic.
    *   `app/main.py`: Main FastAPI application, API endpoints, and HTML route handlers.
    *   `app/models.py`: SQLAlchemy ORM models defining the database schema.
    *   `app/schemas.py`: Pydantic schemas for data validation and serialization.
    *   `app/simulator.py`: Dungeon expedition simulation logic.
    *   `app/progression.py`: Adventurer progression and leveling logic.
    *   `app/templates/`: Jinja2 HTML templates for rendering the UI.
        *   `app/templates/partials/`: Reusable HTML partials.
*   `static/`: Static assets like CSS and images.
*   `data/`: Contains the SQLite database file.
*   `tests/`: Unit and integration tests for the application.
*   `.venv/`: Python virtual environment.
*   `requirements.txt`: Project dependencies.

## 4. Development Workflow

### Running the Application

To start the development server:
```bash
uvicorn app.main:app --reload
```
The application will typically be accessible at `http://127.0.0.1:8000`.

### Running Tests

Tests are written using Pytest. To run all tests:
```bash
pytest
```
Specific test files can be run by providing their path:
```bash
pytest tests/test_main_utils.py
```

### Linting/Formatting

While no explicit linting tool is configured in `requirements.txt`, adhere to PEP 8 guidelines. Common tools for Python include `ruff` or `flake8` for linting, and `black` for formatting. If changes are made, consider running:
```bash
ruff check .
black .
```
(Note: These tools are not currently installed as project dependencies, but are common Python best practices.)

## 5. Coding Standards and Conventions

*   **Python:** Adhere to PEP 8 for code style.
*   **FastAPI:** Follow FastAPI's best practices for structuring routes, dependencies, and Pydantic models.
*   **SQLAlchemy:** Use the ORM for database interactions.
*   **Jinja2/HTMX:**
    *   Keep templates clean and focused on presentation.
    *   Utilize HTMX attributes for dynamic content loading and form submissions.
    *   Ensure proper context is passed to templates and partials.
*   **Error Handling:** Implement robust error handling for API endpoints and database operations.
*   **Comments:** Add comments to explain complex logic or non-obvious design choices.

## 6. Database Information

*   **Type:** SQLite
*   **Location:** `data/db.sqlite`
*   **Schema:** Defined in `app/models.py`. `Base.metadata.create_all(bind=engine)` is used to create tables on application startup if they don't exist.

## 7. Important Notes for AI

*   **Context is Key:** Always read relevant files (models, schemas, related templates, and API endpoints) before making changes.
*   **HTMX Interactions:** Pay close attention to `hx-*` attributes in HTML templates, as they define the dynamic behavior and expected responses from FastAPI endpoints.
*   **Database Migrations:** This project does not currently use a database migration tool (e.g., Alembic). Be cautious with schema changes that might break existing data.
*   **Simulator:** The `app/simulator.py` module contains core game logic. Changes here can significantly impact game balance and behavior.
*   **Frontend/Backend Integration:** Many HTML routes return partials (`partials/*.html`) which are then swapped into the DOM by HTMX. Ensure that the data returned by the backend matches the expectations of the frontend templates.

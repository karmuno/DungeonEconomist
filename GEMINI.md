# DungeonEconomist - AI Agent Guidelines

This document provides guidelines and context for AI agents interacting with the DungeonEconomist codebase.

## 1. Project Overview

DungeonEconomist is a D&D party management game being rebuilt with a Flask backend, a Vue.js frontend, OpenAPI for API documentation, and deployed on Google Cloud Run.

## 2. Technology Stack

*   **Backend:** Python 3.10+, Flask, SQLAlchemy (ORM), Flask-OpenAPI3
*   **Frontend:** Vue.js, JavaScript/TypeScript
*   **Database:** SQLite (`data/db.sqlite`)
*   **Deployment:** Google Cloud Run, Docker
*   **Testing:** Pytest (for backend), Jest/Vue Test Utils (for frontend - to be set up)

## 3. Directory Structure

*   `backend/`: Contains the Flask backend application.
    *   `backend/app.py`: Main Flask application, API endpoints, and OpenAPI integration.
    *   `backend/models.py`: SQLAlchemy ORM models.
    *   `backend/schemas.py`: Pydantic/Marshmallow schemas for data validation and serialization.
    *   `backend/services.py`: Business logic and helper functions.
    *   `backend/requirements.txt`: Backend Python dependencies.
    *   `backend/Dockerfile`: Dockerfile for containerizing the Flask app.
*   `frontend/`: Contains the Vue.js frontend application.
    *   `frontend/src/`: Vue.js source code.
    *   `frontend/public/`: Static assets for Vue.js.
    *   `frontend/package.json`: Frontend dependencies and scripts.
*   `data/`: Contains the SQLite database file.
*   `tests/`: Unit and integration tests for both backend and frontend.
*   `.venv/`: Python virtual environment (for backend).
*   `buildplans/`: Project build and design documents.
*   `docs/`: (Optional) Additional documentation, e.g., OpenAPI specification files.

## 4. Development Workflow

### Running the Application

#### Backend (Flask)
To start the development server:
```bash
cd backend
source venv/bin/activate # On Windows: venv\Scripts\activate
flask run
```
The Flask API will typically be accessible at `http://127.0.0.1:5000`.
Interactive API docs (Swagger UI) at `http://127.0.0.1:5000/openapi/swagger`.

#### Frontend (Vue.js)
To start the development server:
```bash
cd frontend
npm run serve # or yarn serve
```
The Vue.js application will typically be accessible at `http://localhost:8080`.

### Running Tests

#### Backend Tests (Pytest)
```bash
cd backend
source venv/bin/activate
pytest
```
Specific test files can be run by providing their path:
```bash
pytest tests/test_some_module.py
```

#### Frontend Tests (Jest/Vue Test Utils - to be set up)
```bash
cd frontend
npm test # or yarn test
```

### Linting/Formatting

#### Python (Backend)
Adhere to PEP 8 guidelines. Common tools include `ruff` or `flake8` for linting, and `black` for formatting.
```bash
ruff check backend/
black backend/
```

#### JavaScript/Vue (Frontend)
ESLint and Prettier will be configured for the Vue.js project.
```bash
cd frontend
npm run lint # or yarn lint
```

## 5. Coding Standards and Conventions

*   **Python:** Adhere to PEP 8 for code style.
*   **Flask:** Follow Flask best practices for structuring applications, blueprints, and extensions.
*   **SQLAlchemy:** Use the ORM for database interactions.
*   **OpenAPI:** Ensure API endpoints are properly documented with OpenAPI specifications.
*   **Vue.js:** Follow Vue.js style guide and best practices for component structure, state management, and routing.
*   **Error Handling:** Implement robust error handling for API endpoints and database operations.
*   **Comments:** Add comments to explain complex logic or non-obvious design choices.

## 6. Database Information

*   **Type:** SQLite
*   **Location:** `data/db.sqlite`
*   **Schema:** Defined in `backend/models.py`. `Base.metadata.create_all(bind=engine)` is used to create tables on application startup if they don't exist.

## 7. Important Notes for AI

*   **Context is Key:** Always read relevant files (models, schemas, related API endpoints, and frontend components) before making changes.
*   **API Contract:** The Flask backend and Vue.js frontend communicate via the OpenAPI-defined API. Ensure any changes to the backend API are reflected in the OpenAPI specification and communicated to the frontend.
*   **Database Migrations:** This project does not currently use a database migration tool (e.g., Alembic). Be cautious with schema changes that might break existing data.
*   **Simulator:** The core game logic (e.g., `simulator.py`, `progression.py`) will likely be moved to `backend/services.py` or similar. Changes here can significantly impact game balance and behavior.
*   **Deployment:** Remember the Google Cloud Run deployment strategy. Changes should be container-friendly.
*   **Debugging Background Processes:** When running applications in the background (e.g., using `&` with `run_shell_command`), always ensure there's a clear way to retrieve logs or run the process in the foreground for debugging. If an application is misbehaving in the background, stop it immediately and restart it in the foreground to capture detailed error messages and stack traces. Avoid getting stuck in a loop of re-running background processes without understanding the underlying issue.
*   **Quality Assurance:** Always ensure changes pass linting and unit tests. Prioritize writing unit tests *before* implementing any new code (Test-Driven Development - TDD).

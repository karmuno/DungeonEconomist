# Refactoring Plan: Transition to Vue.js, Flask, OpenAPI, and Google Cloud Run

## Introduction

This document outlines a comprehensive plan to refactor the existing DungeonEconomist application from its current FastAPI/Jinja2/HTMX architecture to a modern full-stack setup utilizing Vue.js for the frontend, Flask for the backend API, OpenAPI for API documentation, and Google Cloud Run for serverless deployment. The goal is to enhance scalability, maintainability, and developer experience.

## Current Architecture Overview

*   **Backend:** FastAPI (Python)
*   **Frontend:** Jinja2 templates with HTMX for dynamic UI updates
*   **Database:** SQLite (`data/db.sqlite`)
*   **Core Logic:** `app/main.py` handles both API endpoints and HTML route rendering.

## Target Architecture Overview

*   **Frontend:** Vue.js single-page application (SPA)
*   **Backend API:** Flask (Python)
*   **API Specification:** OpenAPI 3.0
*   **Deployment:** Google Cloud Run (containerized services)
*   **Database:** (Optional but Recommended) Google Cloud SQL

## Refactoring Phases and Steps

### Phase 1: Backend API Transformation (FastAPI to Flask with OpenAPI)

This phase focuses on migrating the existing backend logic from FastAPI to Flask and integrating OpenAPI for API definition and documentation.

#### 1.1. Flask Project Setup and Core Logic Migration

*   **Action:** Initialize a new Flask project structure.
    *   Create a new directory for the Flask backend (e.g., `backend/`).
    *   Set up a basic Flask application (`backend/app.py`).
*   **Action:** Migrate SQLAlchemy ORM models.
    *   Copy `app/models.py` to `backend/models.py`.
    *   Adjust imports and SQLAlchemy setup to be Flask-compatible (e.g., using Flask-SQLAlchemy if desired, or managing sessions manually as currently done).
*   **Action:** Recreate existing endpoints as RESTful API endpoints.
    *   Analyze `app/main.py` to identify all API endpoints (e.g., `/adventurers/`, `/parties/`, `/expeditions/`).
    *   For each endpoint, create corresponding Flask routes (`@app.route(...)`) in `backend/app.py`.
    *   Ensure data is returned as JSON, as the frontend will now be a JavaScript application consuming APIs.
    *   Replace `Form(...)` dependencies with request body parsing (e.g., `request.get_json()` or using a library like `webargs`).
*   **Action:** Migrate business logic and helper functions.
    *   Move `add_progression_data`, `calculate_loot_split`, `check_for_level_up`, `calculate_hp_gain`, `get_class_level_bonuses` from `app/main.py` and other `app/` files into appropriate modules within the `backend/` structure (e.g., `backend/services/`, `backend/utils/`).
    *   Adjust imports accordingly.

#### 1.2. OpenAPI Integration

*   **Action:** Choose and integrate a Flask OpenAPI library.
    *   Popular choices include `flask-openapi3` or `flasgger`.
    *   Install the chosen library (`pip install flask-openapi3`).
    *   Configure the Flask application to generate OpenAPI specifications automatically from route decorators and Pydantic models (or Marshmallow schemas).
*   **Action:** Define API schemas.
    *   Copy and adapt Pydantic schemas from `app/schemas.py` to be used with the chosen OpenAPI library (e.g., directly with `flask-openapi3` or convert to Marshmallow schemas for `flasgger`).
*   **Action:** Verify interactive API documentation.
    *   Run the Flask application and ensure Swagger UI (or ReDoc) is accessible at the configured path (e.g., `/docs` or `/redoc`).
    *   Confirm that all API endpoints are correctly documented with their parameters, request bodies, and responses.

### Phase 2: Frontend Re-implementation (Jinja2/HTMX to Vue.js)

This phase involves rebuilding the user interface as a separate Vue.js single-page application.

#### 2.1. Vue.js Project Setup

*   **Action:** Initialize a new Vue.js project.
    *   Use Vue CLI (`vue create frontend/`) or Vite (`npm create vue@latest frontend/`) to scaffold a new Vue.js project in a separate `frontend/` directory.
*   **Action:** Set up frontend routing.
    *   Install Vue Router (`npm install vue-router`).
    *   Define routes for each main view (e.g., `/`, `/adventurers`, `/parties`, `/expeditions`).
*   **Action:** Set up state management (if necessary).
    *   For complex application state, consider installing Vuex (`npm install vuex`) or Pinia (`npm install pinia`).

#### 2.2. UI Component Development

*   **Action:** Rebuild existing HTML pages/partials as Vue components.
    *   For each Jinja2 template (`index.html`, `adventurers.html`, `parties.html`, `partials/*.html`), create a corresponding Vue component (`.vue` file).
    *   Translate Jinja2 templating logic (`{% if %}`, `{% for %}`) into Vue.js directives (`v-if`, `v-for`).
    *   Replace HTMX attributes (`hx-get`, `hx-post`, `hx-target`, `hx-swap`) with Vue.js component methods that make API calls to the new Flask backend using `axios` or the native `fetch` API.
*   **Action:** Implement forms for creating/editing entities.
    *   Create Vue components for party creation/editing, adventurer creation, etc.
    *   Handle form input binding (`v-model`) and submission logic.
    *   Manage modal display state within Vue.js components.
*   **Action:** Adapt dynamic content updates.
    *   Re-implement dynamic list filtering/sorting and time panel updates using Vue.js reactivity and API calls.

### Phase 3: Deployment to Google Cloud Run

This phase focuses on containerizing the backend and deploying both frontend and backend services to Google Cloud Run.

#### 3.1. Backend Containerization

*   **Action:** Create a `Dockerfile` for the Flask application.
    *   Define a base image (e.g., `python:3.10-slim-buster`).
    *   Copy application code and install dependencies (`pip install -r requirements.txt`).
    *   Expose the port Flask listens on (e.g., `EXPOSE 8080`).
    *   Define the entrypoint command to run the Flask application (e.g., `CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app`).
*   **Action:** Build and test the Docker image locally.
    *   `docker build -t dungeon-economist-backend .`
    *   `docker run -p 8080:8080 dungeon-economist-backend`

#### 3.2. Frontend Build and Hosting

*   **Action:** Build the Vue.js application for production.
    *   Navigate to the `frontend/` directory and run `npm run build`.
    *   This will generate static files in a `dist/` directory.
*   **Action:** Choose a hosting strategy for the frontend:
    *   **Option A (Recommended for static assets):** Deploy built Vue.js files to Google Cloud Storage and serve via Cloud CDN.
        *   Create a Cloud Storage bucket.
        *   Upload the contents of `frontend/dist/` to the bucket.
        *   Configure the bucket for static website hosting.
        *   Set up Cloud CDN for improved performance and caching.
    *   **Option B (Alternative - simpler for initial deployment):** Serve Vue.js static files from the Flask backend.
        *   Copy the `frontend/dist/` contents into a `static/` folder within the Flask backend.
        *   Configure Flask to serve these static files.
        *   This means the Flask container will serve both the API and the frontend.
    *   **Option C (Separate Cloud Run Service):** Deploy the Vue.js app as a separate Cloud Run service using a lightweight web server like Nginx or Caddy in a Docker container.

#### 3.3. Cloud Run Deployment

*   **Action:** Push Flask Docker image to Google Container Registry (GCR) or Artifact Registry.
    *   `gcloud auth configure-docker`
    *   `docker tag dungeon-economist-backend gcr.io/your-gcp-project-id/dungeon-economist-backend:latest`
    *   `docker push gcr.io/your-gcp-project-id/dungeon-economist-backend:latest`
*   **Action:** Deploy the Flask service to Cloud Run.
    *   `gcloud run deploy dungeon-economist-backend --image gcr.io/your-gcp-project-id/dungeon-economist-backend:latest --platform managed --region us-central1 --allow-unauthenticated --port 8080`
*   **Action:** Configure environment variables.
    *   Set database connection strings or other sensitive information as Cloud Run environment variables.
*   **(Optional) Action:** Set up Google Cloud Endpoints or API Gateway.
    *   Define an OpenAPI specification for your API.
    *   Deploy the OpenAPI spec to Cloud Endpoints/API Gateway to enable features like API key management, authentication, and traffic management.

### Phase 4: Database Migration (Optional but Recommended)

For a production-ready cloud application, migrating from SQLite to a managed database service is highly recommended.

*   **Action:** Choose a managed database service.
    *   Google Cloud SQL (PostgreSQL or MySQL) is a strong candidate.
*   **Action:** Migrate existing data (if any).
    *   Export data from SQLite.
    *   Import data into Cloud SQL.
*   **Action:** Update backend database connection.
    *   Modify `backend/app.py` (or Flask-SQLAlchemy configuration) to connect to Cloud SQL instead of SQLite.

## Workflow Summary (Revised)

1.  Develop Vue.js frontend and Flask backend separately.
2.  Integrate OpenAPI specification generation into the Flask application.
3.  Build the Vue.js frontend for production.
4.  Dockerize the Flask backend.
5.  Deploy the Flask backend container to Google Cloud Run.
6.  Deploy the Vue.js static files (e.g., to Cloud Storage + Cloud CDN, or as a separate Cloud Run service).
7.  (Optional) Configure Google Cloud Endpoints or API Gateway to manage and secure the Flask API.
8.  (Optional) Migrate SQLite database to Google Cloud SQL.

## Considerations and Challenges

*   **CORS:** Ensure proper Cross-Origin Resource Sharing (CORS) configuration in the Flask backend to allow requests from the Vue.js frontend.
*   **Authentication:** Implement a robust authentication and authorization mechanism (e.g., JWT-based authentication) for API access.
*   **State Management:** Carefully plan state management in the Vue.js application to avoid complexity as the application grows.
*   **Error Handling:** Implement comprehensive error handling on both frontend and backend.
*   **Testing:** Develop unit and integration tests for both frontend and backend components.
*   **CI/CD:** Set up Continuous Integration/Continuous Deployment pipelines for automated builds, tests, and deployments to Cloud Run.
*   **Environment Variables:** Manage environment-specific configurations (API keys, database URLs) securely.

This plan provides a high-level roadmap. Each step will require detailed implementation and testing.
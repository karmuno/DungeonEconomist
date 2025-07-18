# DungeonEconomist

DungeonEconomist is a Dungeons & Dragons (D&D) inspired party management simulation game. This project is being rebuilt with a Flask backend, a Vue.js frontend, OpenAPI for API documentation, and deployed on Google Cloud Run.

## Features
- Manage adventurers of different classes, track their progression, and manage their equipment.
- Level up characters to improve their stats and gain class-specific benefits.
- Create parties and assign adventurers for expeditions.
- Simulate dungeon expeditions, tracking XP, loot, HP changes, and view detailed results.
- Manage party supplies and funds.
- Experience a dynamic loot system where treasure is split between adventurers and a central player treasury.
- Track a player score based on accumulated wealth in the treasury.
- Advance game time, triggering periodic upkeep costs for adventurers.
- Handle adventurer bankruptcy if they cannot afford upkeep.
- Persistent game state stored in a SQLite database.

## Architecture

The application follows a microservices-like architecture:

1.  **Vue.js (Frontend)**:
    *   Serves as the user interface.
    *   Developed separately and built into static HTML, CSS, and JavaScript files.
2.  **Flask (Backend API)**:
    *   Provides the backend API, handling business logic and data interactions.
    *   Exposes API endpoints for the Vue frontend to consume.
    *   Uses OpenAPI for API documentation and specification.
3.  **OpenAPI (API Documentation and Specification)**:
    *   Defines and documents the Flask API, providing interactive documentation (e.g., Swagger UI).
4.  **Google Cloud Run (Deployment)**:
    *   Serverless platform for deploying containerized applications.
    *   The Flask backend will be containerized and deployed here.
    *   The Vue.js static files can be served from a separate Cloud Run service or Google Cloud Storage + Cloud CDN.
5.  **API Gateway (Optional)**:
    *   For managing and securing the API (e.g., Google Cloud Endpoints).

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/DungeonEconomist.git
    cd DungeonEconomist
    ```
2.  **Backend Setup**:
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Frontend Setup**:
    ```bash
    cd ../frontend
    npm install # or yarn install
    ```

## Running the Project

### Backend (Flask)

1.  Navigate to the `backend/` directory:
    ```bash
    cd backend
    ```
2.  Activate your virtual environment:
    ```bash
    source venv/bin/activate # On Windows: venv\Scripts\activate
    ```
3.  Run the Flask server:
    ```bash
    flask run
    ```
    This will start the Flask server locally, typically on `http://127.0.0.1:5000`.
    Access the interactive API docs (Swagger UI) at `http://127.0.0.1:5000/openapi/swagger`.

### Frontend (Vue.js)

1.  Navigate to the `frontend/` directory:
    ```bash
    cd frontend
    ```
2.  Run the Vue.js development server:
    ```bash
    npm run serve # or yarn serve
    ```
    This will typically start the Vue.js application on `http://localhost:8080`.

## Resetting the Database

The game uses SQLite database at `./data/db.sqlite`.
To reset:

1.  Stop any running servers (Flask, Vue.js dev server).
2.  Delete or rename the database file:
    ```bash
    rm -f data/db.sqlite
    ```
3.  Restart the Flask server, which will recreate a fresh database with default data.

## Project Structure

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
*   `README.md`: This file.
*   `buildplans/`: Project build and design documents.
*   `docs/`: (Optional) Additional documentation, e.g., OpenAPI specification files.
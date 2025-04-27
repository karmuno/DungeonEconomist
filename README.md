# Venturekeep

        Venturekeep is a Dungeons & Dragons (D&D) inspired party management simulation game built with FastAPI. Players manage adventurers, parties, expeditions, and resources as they
    venture through dungeons, track progress, and collect loot.

        ## Features
        - Manage adventurers of different classes and manage their equipment.
        - Create parties and assign adventurers.
        - Simulate dungeon expeditions with multiple nodes, tracking XP, loot, HP changes, and more.
        - Manage party supplies and funds.
        - Persistent game state stored in a SQLite database.

        ## Installation

        1. Clone the repository.
        2. Create a Python virtual environment (recommended):
           ```bash
           python3 -m venv venv
           source venv/bin/activate  # On Windows: venv\Scripts\activate

        1. Install the dependencies:    pip install -r requirements.txt

    ## Running the Project

    Start the FastAPI server with Uvicorn:

        uvicorn app.main:app --reload

    This will start the server locally on http://127.0.0.1:8000.

    Access the interactive API docs at http://127.0.0.1:8000/docs.

    ## Resetting the Database

    The game uses SQLite database at ./data/db.sqlite.
    To reset:

        1. Stop the running server.
        2. Delete or rename the database file:    rm -f data/db.sqlite
        3. Restart the server, which will recreate a fresh database with default data.

    ## Project Structure

        * `app/`: Source code including models, API routes, simulation, and templates.
        * `data/`: Contains the SQLite database file.
        * `static/`: Static files such as CSS and JS.
        * `requirements.txt`: Python dependencies.
        * `README.md`: This file.
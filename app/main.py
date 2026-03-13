from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.database import create_tables
from app.routes import adventurers, players, parties, expeditions, game

# Create tables on startup
create_tables()

# FastAPI app
app = FastAPI(
    title="Venturekeep",
    description="D&D Party Management Simulation",
    version="0.2.0"
)

# CORS (permissive for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(adventurers.router)
app.include_router(players.router)
app.include_router(parties.router)
app.include_router(expeditions.router)
app.include_router(game.router)

# Serve Vue production build if it exists
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="vue-assets")

    @app.get("/{full_path:path}")
    async def serve_vue(full_path: str):
        """Catch-all route to serve the Vue SPA."""
        # Try to serve the exact file first (e.g., favicon.png)
        file_path = frontend_dist / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

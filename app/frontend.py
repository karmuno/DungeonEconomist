from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def _find_build_file(dist: Path, full_path: str) -> Path | None:
    """Return the file full_path names inside the resolved dist, or None if there isn't one."""
    try:
        # resolve() covers both escapes: ".." segments, and absolute paths replacing dist in the join
        file_path = (dist / full_path).resolve()
    except ValueError:  # null byte in the path
        return None
    if file_path.is_relative_to(dist) and file_path.is_file():
        return file_path
    return None


def mount_frontend(app: FastAPI, frontend_dist: Path) -> None:
    """Serve the Vue production build. Call after every API route is registered."""
    dist = frontend_dist.resolve()
    app.mount("/assets", StaticFiles(directory=str(dist / "assets")), name="vue-assets")

    @app.get("/{full_path:path}")
    async def serve_vue(full_path: str):
        """Catch-all route to serve the Vue SPA."""
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        # Try to serve the exact file first (e.g., favicon.png)
        return FileResponse(_find_build_file(dist, full_path) or dist / "index.html")

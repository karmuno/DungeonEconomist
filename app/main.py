import os
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.frontend import mount_frontend
from app.version import get_app_version

if os.environ.get("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        send_default_pii=True,
        traces_sample_rate=0,
        release=get_app_version(),
        environment=os.environ.get("APP_ENV", "development"),
    )
from app.routes import admin as admin_routes
from app.routes import adventurers, expeditions, game, parties
from app.routes import auth as auth_routes
from app.routes import buildings as buildings_routes
from app.routes import feedback as feedback_routes
from app.routes import keeps as keeps_routes

# Create tables on startup
create_tables()

# FastAPI app
app = FastAPI(
    title="Venturekeep",
    description="Retro RPG Party Management Simulation",
    version=get_app_version(),
)

# CORS — lock down in production, permissive for local dev
_cors_origins_env = os.environ.get("CORS_ORIGINS", "")
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()] if _cors_origins_env else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth_routes.router)
app.include_router(keeps_routes.router)
app.include_router(buildings_routes.router)
app.include_router(admin_routes.router)
app.include_router(adventurers.router)
app.include_router(parties.router)
app.include_router(expeditions.router)
app.include_router(game.router)
app.include_router(feedback_routes.router)

# Serve Vue production build if it exists
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    mount_frontend(app, frontend_dist)

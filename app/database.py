import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    # Only fall back to SQLite for local dev (not in Docker/production).
    if os.environ.get("PORT"):
        raise RuntimeError("DATABASE_URL must be set in production (PORT is set but DATABASE_URL is not)")
    DATABASE_URL = "sqlite:///./data/db.sqlite"

_is_sqlite = DATABASE_URL.startswith("sqlite")

# SQLite needs check_same_thread=False; Postgres does not.
connect_args = {"check_same_thread": False} if _is_sqlite else {}

# Postgres (especially serverless like Neon) benefits from connection health checks.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=not _is_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

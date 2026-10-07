"""
Venturekeep application package
"""

# Load .env before anything else: app.database, app.auth and app.main all read
# os.environ at import time, so this has to happen before any of them are imported.
# Real environment variables always win — python-dotenv does not override them —
# so production, where docker --env-file injects the values, is unaffected.
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

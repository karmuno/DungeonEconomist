"""The running build's version string.

Mirrors ``getAppVersion()`` in ``frontend/vite.config.ts`` so both halves of a
build report the same string, and an error in Sentry names the build it came
from regardless of which side raised it.

Resolution order, most to least authoritative:

1. ``APP_VERSION`` env var — explicit override, and how non-Docker deploys set it.
2. ``version.txt`` at the repo root — baked into the Docker image, which carries
   neither ``.git/`` nor ``scripts/``.
3. ``scripts/get-version.sh`` — development machines, where git is present.
4. The ``VERSION`` file alone — last resort, with no branch stage or build hash.
"""

import os
import subprocess
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def get_app_version() -> str:
    """Return the full version string, e.g. ``v0.9.0-qa+build.a3f2c1d``."""
    env_version = os.environ.get("APP_VERSION")
    if env_version:
        return env_version.strip()

    baked = REPO_ROOT / "version.txt"
    try:
        if baked.is_file():
            return baked.read_text(encoding="utf-8").strip()
    except OSError:
        pass

    try:
        result = subprocess.run(
            ["bash", "scripts/get-version.sh"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        if result.stdout.strip():
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass

    try:
        return f"v{(REPO_ROOT / 'VERSION').read_text(encoding='utf-8').strip()}"
    except OSError:
        return "v0.0.0-unknown"

"""Hook helper: run full lint on the project.

Used by the Stop hook and pre-commit hook.
Runs ruff on Python files and eslint on frontend files.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    errors = False

    # Python: ruff
    print("Running ruff check...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "app/", "tests/"],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        errors = True

    # Frontend: eslint
    print("Running eslint...")
    result = subprocess.run(
        ["npx", "eslint", "src/"],
        cwd=str(PROJECT_ROOT / "frontend"),
        shell=True,
    )
    if result.returncode != 0:
        errors = True

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

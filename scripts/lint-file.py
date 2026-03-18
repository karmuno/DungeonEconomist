"""Hook helper: lint a single file based on its extension.

Reads Claude Code hook JSON from stdin, extracts the file path,
and runs the appropriate linter (ruff for .py, eslint for .vue/.ts).
"""

import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    file_path = data.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return

    p = Path(file_path)

    if p.suffix == ".py":
        subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", str(p)],
            capture_output=True,
        )
    elif p.suffix in (".vue", ".ts", ".tsx"):
        # Run eslint from the frontend directory
        frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
        subprocess.run(
            ["npx", "eslint", "--fix", str(p)],
            cwd=str(frontend_dir),
            capture_output=True,
            shell=True,
        )


if __name__ == "__main__":
    main()

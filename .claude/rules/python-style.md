---
description: Python code style conventions for backend and tests
globs: ["app/**/*.py", "tests/**/*.py"]
---

# Python Style

- Follow PEP 8. Enforced by ruff (see `pyproject.toml` for config).
- Imports: stdlib first, then third-party, then local. Enforced by ruff isort rules.
- Use type hints for all function parameters and return values.
- SQLAlchemy models in `app/models.py` — snake_case table/column names.
- Pydantic schemas in `app/schemas.py` — PascalCase class names.
- Error handling: raise `fastapi.HTTPException` in route handlers.
- Use Python `enum.Enum` for enumerations.
- Docstrings: `"""triple quotes"""` for classes and public functions.
- Max line length: 120 characters.

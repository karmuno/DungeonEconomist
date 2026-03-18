---
description: Testing conventions
globs: ["tests/**/*.py"]
---

# Testing

- Framework: pytest with httpx `TestClient`.
- Test files: `tests/test_*.py`.
- Each test gets a fresh database (test fixtures handle setup/teardown).
- Run all tests: `pytest tests/`
- Run one test: `pytest tests/test_sim.py::test_name`
- Tests must pass before committing.

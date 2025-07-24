## Backend (Python)

- **Run:** `make run-backend`
- **Test:** `make test-backend`
- **Run single test:** `.venv/bin/python -m pytest -s src/backend/tests/unit/core/test_manager.py`
- **Linting:** `ruff check .` and `ruff format .` (based on pyproject.toml)
- **Style:**
  - Use FastAPI for web APIs.
  - Use Pydantic for data models.
  - Use `uv` for dependency management.
  - Follow Black formatting and ruff for linting.
  - Use Google-style docstrings.
  - Type hints are required.

## Frontend (TypeScript/React)

- **Run:** `make run-frontend`
- **Build:** `cd src/frontend && yarn build`
- **Lint:** `cd src/frontend && yarn lint`
- **Style:**
  - Use React with Vite.
  - Use TypeScript with `.tsx` for components.
  - Use CSS modules for styling.
  - Follow Prettier for formatting and ESLint for linting.

.PHONY: help install-backend run-backend install-frontend run-frontend install

help:
	@echo "Commands:"
	@echo "  install          : Install all dependencies for backend and frontend."
	@echo "  install-backend  : Install backend dependencies."
	@echo "  run-backend      : Start backend development server on http://localhost:8000."
	@echo "  install-frontend : Install frontend dependencies."
	@echo "  run-frontend     : Start frontend development server on http://localhost:5173."
	@echo "  dev              : Run 'make run-backend' and 'make run-frontend' in separate terminals to start development."

# ====================================================================================
#  BACKEND
# ====================================================================================

install-backend:
	@echo ">>> Installing backend dependencies..."
	@uv pip install -r src/backend/requirements.txt --python .venv/bin/python

run-backend:
	@echo ">>> Starting backend development server..."
	@uv run --cwd src/backend dev --python .venv/bin/python

# ====================================================================================
#  FRONTEND
# ====================================================================================

install-frontend:
	@echo ">>> Installing frontend dependencies..."
	@cd src/frontend && yarn install

run-frontend:
	@echo ">>> Starting frontend development server..."
	@cd src/frontend && yarn dev

# ====================================================================================
#  PROJECT
# ====================================================================================

install: install-backend install-frontend

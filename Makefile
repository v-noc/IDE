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

start-db:
	@echo ">>> Starting ArangoDB..."
	@docker-compose -f src/backend/docker-compose.yml --env-file src/backend/.env up -d

stop-db:
	@echo ">>> Stopping ArangoDB..."
	@docker-compose -f src/backend/docker-compose.yml --env-file src/backend/.env down

run-backend: start-db
	@echo ">>> Starting backend development server..."
	@cd src/backend && ../../.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test-backend:
	@echo ">>> Running backend tests..."
	@.venv/bin/python -m pytest src/backend/tests

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

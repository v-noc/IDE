.PHONY: help install-backend run-backend install-frontend run-frontend install start-db stop-db \
	install-lsp-python install-lsp-ts install-lsp run-lsp-python run-lsp-ts run-lsp

help:
	@echo "Commands:"
	@echo "  install          : Install all dependencies for backend and frontend."
	@echo "  install-backend  : Install backend dependencies."
	@echo "  start-db         : Start TerminusDB (Docker) on http://localhost:6363."
	@echo "  stop-db          : Stop TerminusDB."
	@echo "  run-backend      : Start backend development server on http://localhost:8000."
	@echo "  run-rpc          : Start JSON-RPC server on http://localhost:8050/api/v1/jsonrpc."
	@echo "  run-servers      : Start backend and JSON-RPC servers."
	@echo "  install-frontend : Install frontend dependencies."
	@echo "  run-frontend     : Start frontend development server on http://localhost:5173."
	@echo "  install-lsp      : Install language driver deps (Python + TS/JS)."
	@echo "  run-lsp-python   : Start Python driver JSON-RPC (uvicorn; READY port=...)."
	@echo "  run-lsp-ts       : Start TS/JS driver JSON-RPC on http://127.0.0.1:9001/rpc (bun)."
	@echo "  run-lsp          : Start Python and TS/JS drivers in parallel."
	@echo "  dev              : Run 'make run-backend' and 'make run-frontend' in separate terminals to start development."

# ====================================================================================
#  BACKEND
# ====================================================================================

install-backend:
	@echo ">>> Installing backend dependencies..."
	@uv pip install -r src/backend/requirements.txt --python .venv/bin/python

start-db:
	@echo ">>> Starting TerminusDB..."
	@docker compose -f src/backend/docker-compose.yml --env-file src/backend/.env up -d

stop-db:
	@echo ">>> Stopping TerminusDB..."
	@docker compose -f src/backend/docker-compose.yml --env-file src/backend/.env down

run-backend: start-db
	@echo ">>> Starting backend development server..."
	@cd src/backend && ../../.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-rpc: start-db
	@echo ">>> Starting JSON-RPC server..."
	@cd src/backend && ../../.venv/bin/python -m uvicorn app.api.json_rpc.app:app --reload --host 0.0.0.0 --port 8050

test-backend:
	@echo ">>> Running backend tests..."
	@cd src/backend && ../../.venv/bin/python -m pytest -s tests

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

run-servers:
	@echo ">>> Starting backend (8000) and JSON-RPC (8050) servers..."
	@$(MAKE) -j2 run-backend run-rpc

# ====================================================================================
#  LSP / language drivers (src/lsp)
# ====================================================================================

install-lsp-python:
	@echo ">>> Installing Python language driver (editable)..."
	@uv pip install -e src/lsp/py --python .venv/bin/python

install-lsp-ts:
	@echo ">>> Installing TS/JS language driver dependencies (bun)..."
	@cd src/lsp/ts_js && bun install

install-lsp: install-lsp-python install-lsp-ts

run-lsp-python:
	@echo ">>> Starting Python language driver..."
	@cd src/lsp/py && ../../../.venv/bin/python -m vnoc_lsp_python

run-lsp-ts:
	@echo ">>> Starting TS/JS language driver (default --port 9001)..."
	@cd src/lsp/ts_js && bun run start

run-lsp:
	@echo ">>> Starting Python and TS/JS language drivers..."
	@$(MAKE) -j2 run-lsp-python run-lsp-ts

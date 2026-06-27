# ======================================================================
#  V-NOC — Graph Based IDE
# ----------------------------------------------------------------------
#  All developer entry points are defined here. Run `make help` for a
#  grouped list of available commands.
#
#  Conventions
#    install-*   Install dependencies for a component
#    run-*       Start a long-running process (dev server)
#    start-*     Bring an infra service up (Docker, daemons)
#    stop-*      Tear an infra service down
#    test-*      Run a test suite
# ======================================================================

PY              ?= .venv/bin/python
UV              ?= uv

BACKEND_DIR     := src/backend
FRONTEND_DIR    := src/frontend
LSP_PY_DIR      := src/lsp/py
LSP_TS_DIR      := src/lsp/ts_js

DB_COMPOSE      := $(BACKEND_DIR)/docker-compose.yml
DB_ENV          := $(BACKEND_DIR)/.env

# Default ports (override on the command line, e.g. `make run-backend PORT=9000`)
BACKEND_PORT    ?= 8000
RPC_PORT        ?= 8050
FRONTEND_PORT   ?= 5173
LSP_PY_PORT     ?= 9002
LSP_TS_PORT     ?= 9001
TERMINUS_PORT   ?= 6363

.DEFAULT_GOAL := help

.PHONY: help \
        install install-backend install-frontend install-lsp install-lsp-python install-lsp-ts \
        start-db stop-db reset-db \
        run-backend run-rpc run-servers run-frontend dev \
        run-lsp run-lsp-python run-lsp-ts \
        test test-backend \
        clean

# ----------------------------------------------------------------------
#  HELP
# ----------------------------------------------------------------------

help:
	@echo ""
	@echo "  V-NOC — Graph Based IDE"
	@echo "  ─────────────────────────────────────────────────────────────"
	@echo ""
	@echo "  Setup"
	@echo "    install            Install backend + frontend dependencies"
	@echo "    install-backend    Install backend Python deps (uv)"
	@echo "    install-frontend   Install frontend JS deps (yarn)"
	@echo "    install-lsp        Install all language driver deps"
	@echo "    install-lsp-python Install Python language driver (editable)"
	@echo "    install-lsp-ts     Install TS/JS language driver (bun)"
	@echo ""
	@echo "  Database (TerminusDB — graph + version control)"
	@echo "    start-db           Start TerminusDB on http://localhost:$(TERMINUS_PORT)"
	@echo "    stop-db            Stop TerminusDB"
	@echo "    reset-db           Stop TerminusDB and remove its volume"
	@echo ""
	@echo "  Development servers"
	@echo "    dev                Backend + RPC + frontend (parallel)"
	@echo "    run-backend        REST API on http://localhost:$(BACKEND_PORT)"
	@echo "    run-rpc            JSON-RPC API on http://localhost:$(RPC_PORT)/api/v1/jsonrpc"
	@echo "    run-servers        Backend + RPC (parallel)"
	@echo "    run-frontend       Vite dev server on http://localhost:$(FRONTEND_PORT)"
	@echo ""
	@echo "  Language drivers (LSP-style JSON-RPC adapters)"
	@echo "    run-lsp            Python + TS/JS drivers (parallel)"
	@echo "    run-lsp-python     Python driver  (port \$$LSP_PY_PORT = $(LSP_PY_PORT))"
	@echo "    run-lsp-ts         TS/JS driver   (port \$$LSP_TS_PORT = $(LSP_TS_PORT))"
	@echo ""
	@echo "  Quality"
	@echo "    test               Run all test suites"
	@echo "    test-backend       Run backend pytest suite"
	@echo "    clean              Remove caches and build artefacts"
	@echo ""
	@echo "  Tip: override defaults inline, e.g. \`make run-backend BACKEND_PORT=9000\`"
	@echo ""

# ----------------------------------------------------------------------
#  BACKEND
# ----------------------------------------------------------------------

install-backend:
	@echo ">>> Installing backend dependencies"
	@$(UV) pip install -r $(BACKEND_DIR)/requirements.txt --python $(PY)

run-backend: start-db
	@echo ">>> Backend API → http://localhost:$(BACKEND_PORT)"
	@cd $(BACKEND_DIR) && ../../$(PY) -m uvicorn app.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

run-rpc: start-db
	@echo ">>> JSON-RPC API → http://localhost:$(RPC_PORT)/api/v1/jsonrpc"
	@cd $(BACKEND_DIR) && ../../$(PY) -m uvicorn app.api.json_rpc.app:app --reload --host 0.0.0.0 --port $(RPC_PORT)

run-servers:
	@echo ">>> Starting backend ($(BACKEND_PORT)) and JSON-RPC ($(RPC_PORT))"
	@$(MAKE) -j2 run-backend run-rpc

test-backend:
	@echo ">>> Running backend tests"
	@cd $(BACKEND_DIR) && ../../$(PY) -m pytest -s tests

# ----------------------------------------------------------------------
#  FRONTEND
# ----------------------------------------------------------------------

install-frontend:
	@echo ">>> Installing frontend dependencies"
	@cd $(FRONTEND_DIR) && yarn install

run-frontend:
	@echo ">>> Frontend dev server → http://localhost:$(FRONTEND_PORT)"
	@cd $(FRONTEND_DIR) && yarn dev

# ----------------------------------------------------------------------
#  DATABASE (TerminusDB)
# ----------------------------------------------------------------------

start-db:
	@echo ">>> TerminusDB → http://localhost:$(TERMINUS_PORT)"
	@docker compose -f $(DB_COMPOSE) --env-file $(DB_ENV) up -d

stop-db:
	@echo ">>> Stopping TerminusDB"
	@docker compose -f $(DB_COMPOSE) --env-file $(DB_ENV) down

reset-db:
	@echo ">>> Resetting TerminusDB (volumes will be deleted)"
	@docker compose -f $(DB_COMPOSE) --env-file $(DB_ENV) down -v

# ----------------------------------------------------------------------
#  LANGUAGE DRIVERS  (src/lsp/*)
# ----------------------------------------------------------------------

install-lsp: install-lsp-python install-lsp-ts

install-lsp-python:
	@echo ">>> Installing Python language driver (editable)"
	@$(UV) pip install -e $(LSP_PY_DIR) --python $(PY)

install-lsp-ts:
	@echo ">>> Installing TS/JS language driver"
	@cd $(LSP_TS_DIR) && bun install

run-lsp-python:
	@echo ">>> Python language driver → http://127.0.0.1:$(LSP_PY_PORT)/rpc"
	@cd $(LSP_PY_DIR) && ../../../$(PY) -m vnoc_lsp_python --port $(LSP_PY_PORT)

run-lsp-ts:
	@echo ">>> TS/JS language driver → http://127.0.0.1:$(LSP_TS_PORT)/rpc"
	@cd $(LSP_TS_DIR) && bun run start -- --port $(LSP_TS_PORT)

run-lsp:
	@echo ">>> Starting Python and TS/JS language drivers"
	@$(MAKE) -j2 run-lsp-python run-lsp-ts

# ----------------------------------------------------------------------
#  PROJECT
# ----------------------------------------------------------------------

install: install-backend install-frontend

dev:
	@echo ">>> Backend ($(BACKEND_PORT)) + RPC ($(RPC_PORT)) + Frontend ($(FRONTEND_PORT))"
	@$(MAKE) -j3 run-backend run-rpc run-frontend

test: test-backend

clean:
	@echo ">>> Removing caches and build artefacts"
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	@rm -rf $(FRONTEND_DIR)/dist

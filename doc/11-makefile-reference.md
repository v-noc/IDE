# 11 · Makefile Reference

The [`Makefile`](../Makefile) is the **single entry point** for every dev command in V-NOC. Run `make help` for the human-friendly grouped listing. This page is the exhaustive reference.

---

## Variables

All variables are overridable inline: `make run-backend BACKEND_PORT=9000`.

### Tools

| Variable | Default | Purpose |
|---|---|---|
| `PY` | `.venv/bin/python` | Python interpreter used for backend & Python driver |
| `UV` | `uv` | `uv` binary for dependency installs |

### Paths

| Variable | Default | Component |
|---|---|---|
| `BACKEND_DIR` | `src/backend` | Backend root |
| `FRONTEND_DIR` | `src/frontend` | Frontend root |
| `LSP_PY_DIR` | `src/lsp/py` | Python language driver |
| `LSP_TS_DIR` | `src/lsp/ts_js` | TS/JS language driver |
| `DB_COMPOSE` | `src/backend/docker-compose.yml` | TerminusDB compose file |
| `DB_ENV` | `src/backend/.env` | Compose env-file |

### Ports

| Variable | Default | Service |
|---|---|---|
| `BACKEND_PORT` | `8000` | REST API |
| `RPC_PORT` | `8050` | JSON-RPC API |
| `FRONTEND_PORT` | `5173` | Vite dev server |
| `LSP_PY_PORT` | `9002` | Python language driver |
| `LSP_TS_PORT` | `9001` | TS/JS language driver |
| `TERMINUS_PORT` | `6363` | TerminusDB |

---

## Targets

### Setup

| Target | Does |
|---|---|
| `install` | `install-backend` + `install-frontend` |
| `install-backend` | `uv pip install -r src/backend/requirements.txt` into `.venv` |
| `install-frontend` | `yarn install` inside `src/frontend` |
| `install-lsp` | `install-lsp-python` + `install-lsp-ts` |
| `install-lsp-python` | `uv pip install -e src/lsp/py` |
| `install-lsp-ts` | `bun install` inside `src/lsp/ts_js` |

### Database

| Target | Does |
|---|---|
| `start-db` | `docker compose up -d` for TerminusDB + Vectorlink |
| `stop-db` | `docker compose down` |
| `reset-db` | `docker compose down -v` — **wipes** the TerminusDB volume |

### Development servers

| Target | Does |
|---|---|
| `dev` | `run-backend` + `run-rpc` + `run-frontend` in parallel |
| `run-backend` | `uvicorn app.main:app` on `BACKEND_PORT` (depends on `start-db`) |
| `run-rpc` | `uvicorn app.api.json_rpc.app:app` on `RPC_PORT` (depends on `start-db`) |
| `run-servers` | `run-backend` + `run-rpc` in parallel |
| `run-frontend` | `yarn dev` on `FRONTEND_PORT` |

### Language drivers

| Target | Does |
|---|---|
| `run-lsp` | `run-lsp-python` + `run-lsp-ts` in parallel |
| `run-lsp-python` | Runs `vnoc_lsp_python` on `LSP_PY_PORT` |
| `run-lsp-ts` | Runs the TS/JS driver on `LSP_TS_PORT` |

### Quality

| Target | Does |
|---|---|
| `test` | All test suites (today: `test-backend`) |
| `test-backend` | `pytest -s tests` inside `src/backend` |
| `clean` | Removes `__pycache__`, `.pytest_cache`, and `dist/` |

---

## Recipes

### One-line bootstrap

```bash
uv venv && make install && make install-lsp && cp src/backend/.env.example src/backend/.env && make start-db && make dev
```

### Backend on a different port

```bash
make run-backend BACKEND_PORT=9000
```

### Reset everything (graphs included)

```bash
make stop-db
make reset-db
make clean
```

### Run drivers out-of-process and point the backend at them

```bash
make run-lsp &
echo 'VNOC_LSP_PYTHON_URL=http://127.0.0.1:9002' >> src/backend/.env
echo 'VNOC_LSP_TS_JS_URL=http://127.0.0.1:9001'   >> src/backend/.env
make dev
```

---

## Conventions

The Makefile follows a few rules so it stays maintainable:

- **`install-*`** installs deps for one component.
- **`run-*`** starts a long-running dev process.
- **`start-*` / `stop-*` / `reset-*`** manage infra services (Docker).
- **`test-*`** runs a test suite.
- Targets that need TerminusDB depend on `start-db` directly — you don't need to remember to start it.
- All ports are variables, never hard-coded in recipes.
- Parallel targets use `$(MAKE) -jN`, not `&`, so Ctrl-C tears the whole group down cleanly.

If you add a target, please follow the same conventions and update `make help`.

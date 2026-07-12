# 03 · Getting Started

This page takes you from a clean checkout to a running V-NOC. If you just want the TL;DR, the project [README](../README.md#quick-start) has a three-step version.

---

## Prerequisites

| Tool | Why | Version |
|---|---|---|
| **Python** + [`uv`](https://github.com/astral-sh/uv) | Backend & Python language driver | 3.12+ |
| **Node.js** + Yarn | Frontend | 18+ |
| **Bun** | TS/JS language driver | 1.2+ |
| **Docker** + Docker Compose | TerminusDB + Vectorlink | recent |
| **Make** | The single entry point for every dev command | any |

> [!TIP]
> If you don't have `uv` yet: `curl -LsSf https://astral.sh/uv/install.sh \| sh`.

---

## 1. Clone & install

```bash
git clone <repo-url> v-noc
cd v-noc

uv venv                # creates .venv with the right Python
make install           # backend + frontend deps
make install-lsp       # Python + TS/JS language drivers
```

`make install` is equivalent to running `make install-backend` and `make install-frontend`.

---

## 2. Configure environment

```bash
cp src/backend/.env.example src/backend/.env
```

Defaults (in `.env.example`):

```ini
APP_ENV=development
TERMINUS_HOST=http://localhost:6363
TERMINUS_DB=v_noc
TERMINUS_USER=admin
TERMINUS_KEY=root
TERMINUS_TEAM=admin
TERMINUSDB_ADMIN_PASS=root

PORT=8000

# Optional: pin language driver endpoints
# VNOC_LSP_PYTHON_URL=http://127.0.0.1:9100
# VNOC_LSP_TS_JS_URL=http://127.0.0.1:9200
```

> [!IMPORTANT]
> `TERMINUSDB_ADMIN_PASS` **must** equal `TERMINUS_KEY`. The compose file sets the admin password to `${TERMINUSDB_ADMIN_PASS}`, and the backend authenticates with `TERMINUS_KEY`.

If you set `OPENAI_API_KEY` in the same file, Vectorlink will be able to compute embeddings for semantic search (compose maps it to Vectorlink’s `OPENAI_KEY`). The walkthrough agent uses the same `OPENAI_API_KEY` when `WALKTHROUGH_LLM=openai:…`.

---

## 3. Start the database

```bash
make start-db
```

This starts:

- **TerminusDB** on `http://localhost:6363` (graph + version control)
- **Vectorlink** (semantic indexer) on `http://localhost:8080`

To stop: `make stop-db`. To wipe the volume (you will lose all graphs): `make reset-db`.

---

## 4. Start the dev servers

The simplest path:

```bash
make dev
```

That parallel-runs:

- Backend REST API → `http://localhost:8000`
- Backend JSON-RPC → `http://localhost:8050/api/v1/jsonrpc`
- Frontend (Vite) → `http://localhost:5173`

Open **http://localhost:5173** and you're in.

Need finer-grained control? Run individual servers in separate terminals:

```bash
make run-backend     # REST API only
make run-rpc         # JSON-RPC only
make run-frontend    # Frontend only
make run-servers     # Backend + RPC together
```

### Optional: out-of-process language drivers

For larger projects, or to develop a driver, run them as separate processes:

```bash
make run-lsp           # Python + TS/JS in parallel
# or individually
make run-lsp-python    # → http://127.0.0.1:9002/rpc
make run-lsp-ts        # → http://127.0.0.1:9001/rpc
```

Then point the backend at them via `.env`:

```ini
VNOC_LSP_PYTHON_URL=http://127.0.0.1:9002
VNOC_LSP_TS_JS_URL=http://127.0.0.1:9001
```

See `05-language-drivers.md` for the full picture.

---

## 5. Tests

```bash
make test-backend
```

Suites live in `src/backend/tests/{unit,e2e}`. Pytest config is read from `src/backend/pyproject.toml`.

---

## Override defaults

Every port (and most paths) in the Makefile is variable-driven. Override inline:

```bash
make run-backend BACKEND_PORT=9000
make run-lsp-python LSP_PY_PORT=9500
make start-db TERMINUS_PORT=7000
```

See `11-makefile-reference.md` for the full list.

---

## Common pitfalls

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend exits with `Unauthorized` from TerminusDB | `TERMINUSDB_ADMIN_PASS` ≠ `TERMINUS_KEY` | Make them match in `src/backend/.env` and `make reset-db` |
| `port already in use` | Another process on `8000` / `5173` / etc. | Override the port (see above) |
| TS/JS driver fails to start | Bun not installed | `curl -fsSL https://bun.sh/install \| bash` |
| Project creation fails with `path does not exist` | Path is relative or invalid | Use an **absolute** path, see `04-creating-a-project.md` |
| Frontend can't reach backend | CORS / wrong host | The backend allows `*` by default; check `vite.config.ts` proxy |

Next: [04 · Creating a Project](04-creating-a-project.md).

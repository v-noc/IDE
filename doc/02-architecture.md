# 02 · Architecture

A high-level map of how V-NOC's parts fit together. Each component has its own deep-dive elsewhere; this page exists so you can hold the whole system in your head.

---

## Components at a glance

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Frontend (canvas IDE)                         │
│                          React · Vite · TS — :5173                     │
└───────────────┬───────────────────────────────────────┬───────────────┘
                │ REST + WebSocket                      │ JSON-RPC
                ▼                                       ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│   Backend REST API (:8000)       │     │  Backend JSON-RPC API (:8050)   │
│   FastAPI · Socket.IO            │     │  fastapi-jsonrpc                 │
└───────────────┬─────────────────┘     └───────────────┬─────────────────┘
                │                                       │
                ▼                                       ▼
┌───────────────────────────────────────────────────────────────────────┐
│                       Core (src/backend/app/core)                      │
│                                                                        │
│  parser ─► graph_builder ─► repository ─► services ─► api              │
│      │                          ▲                                      │
│      ▼                          │                                      │
│  language drivers       watcher (filesystem sync)                      │
└──────────────┬──────────────────────────────────────┬─────────────────┘
               │ JSON-RPC                             │ WOQL
               ▼                                      ▼
┌──────────────────────────────┐         ┌───────────────────────────────┐
│  Language drivers (src/lsp/) │         │  TerminusDB (:6363)           │
│   • Python  — Jedi/LibCST    │         │  Graph DB + version control   │
│     :9002                    │         │                               │
│   • TS/JS   — ts-morph/Bun   │         │  Vectorlink (:8080)           │
│     :9001                    │         │  Semantic indexer              │
└──────────────────────────────┘         └───────────────────────────────┘
```

---

## What each layer does

### Frontend — `src/frontend/`
React + Vite canvas IDE. Renders the graph, hosts the agent canvas, surfaces logs / playgrounds / tests / documents per node, and drives all user-initiated actions through the backend.

### Backend REST API — `src/backend/app/api/v1/`
The user-facing HTTP surface. Routers, grouped by domain:

| Prefix | Router | Purpose |
|---|---|---|
| `/projects` | `project_routes.py` | Create / inspect / delete projects |
| `/code-elements` | `code_routes.py` | Nodes (functions, classes, files, folders) |
| `/groups` | `group_routes.py` | Structure groups (user-curated buckets) |
| `/containers` | `container_routes.py` | High-level execution units |
| `/documents` | `document_routes.py` | Docs attached to nodes |
| `/logs` | `logger_routes.py` | Log trees from `vn-logger` |
| `/tests` | `test_routes.py` | Test configuration, runs, cases |
| `/playgrounds` | `play_ground_routes.py` | Sandbox snippets scoped to nodes |
| `/versioning` | `versioning/*.py` | Branches, commits, remotes |
| `/health` | `health.py` | Liveness/readiness |

### Backend JSON-RPC API — `src/backend/app/api/json_rpc/`
The high-throughput surface used by the canvas for fine-grained graph reads/writes that don't map cleanly to REST.

### Core — `src/backend/app/core/`

| Subpackage | Responsibility |
|---|---|
| `parser/` | AST extraction (via drivers), call resolution, MRO resolution |
| `parser/drivers/` | Driver manager, JSON-RPC client, in-process Python driver |
| `graph_builder/` | Orchestration: walk → parse → resolve → insert |
| `model/` | Pydantic + Terminus schemas (`ProjectSchema`, `BaseSchema`, etc.) |
| `repository/` | Read/write helpers over the TerminusDB client |
| `services/` | Application services (`project_service`, `log_service`, `test_service`, `play_ground_service`, `code_element_service`, …) |
| `watcher/` | Filesystem watcher that re-parses files on change |
| `socket/` | Socket.IO emission of graph deltas |
| `sandbox/` | Code execution for playgrounds (`code_run.py`) |
| `builder/` | Tree shaping (paths, neighbourhoods) |
| `cache_setup.py` | FastAPI-Cache initialisation |
| `plugins/` | Plug-in points for cross-cutting features |

### Language drivers — `src/lsp/`
Out-of-process JSON-RPC services that turn source files into language-agnostic AST nodes. See `05-language-drivers.md`.

### Database — TerminusDB
Graph database (WOQL) **with built-in Git-style version control**: branches, commits, diffs, push/pull. Schema is defined in `src/backend/app/core/model/schemas.py` and migrated at startup by `db/client.py::migrate_base`. See `10-version-control.md`.

### Semantic indexer — Vectorlink
Companion service (TerminusDB's `vectorlink`) for embeddings/semantic search. Started by the same Docker Compose file as TerminusDB.

### Structured logger — `src/vn_logger/`
A Python decorator library teams add to their **own** projects so runtime calls show up on the graph. See `07-logs.md`.

---

## Data flow: parsing a project

1. **User** submits `POST /api/v1/projects/` with an absolute `path`.
2. **`ProjectService.create`** writes a `ProjectNode` and kicks off the `GraphBuilderOrchestrator`.
3. **Orchestrator** walks the path, dispatching each source file to the appropriate **language driver** via the driver manager.
4. **Driver** returns AST nodes (`BaseNode[]`), optionally injecting stable IDs into the source (see `06-function-class-tracking.md`).
5. **Orchestrator** resolves calls and MRO using the driver, then **inserts** nodes/edges into TerminusDB through the repository layer.
6. **Watcher** subscribes to the project path. On every file change, the file is re-parsed and the graph delta is emitted over Socket.IO.

---

## Data flow: a runtime log

1. The target project decorates a function with `@context_logger(function_id="…")` from `vn_logger`.
2. On execution, `vn-logger` posts a structured event (chain, parent, args, duration) to the V-NOC JSON-RPC endpoint.
3. The backend persists it via `log_service` and emits a graph delta.
4. The canvas attaches the log to the function node — same id, same chain, same parent.

---

## Persistence model

Everything is graph-shaped. Top-level node types include:

- `ProjectSchema` — the project root
- `BaseSchema` — base type for code elements
- `ThemeConfigSchema` — UI theme per project
- `StructureGroupSchema` — user-curated groupings
- Node types for files, folders, functions, classes, calls, MRO links, logs, tests, playgrounds, documents

Schemas are committed to TerminusDB on backend startup (`migrate_base`).

Next: [03 · Getting Started](03-getting-started.md).

# 05 · Language Drivers

V-NOC keeps the graph builder **language-agnostic** by talking to **language drivers** over JSON-RPC. A driver is a small process that turns source files into AST nodes and answers cross-reference questions. Adding a language means adding a driver, not editing the backend.

---

## What ships today

| Language | Driver path | Engine | Default port |
|---|---|---|---|
| Python | `src/lsp/py/` | [Jedi](https://jedi.readthedocs.io/) + [LibCST](https://libcst.readthedocs.io/) | `9002` |
| TypeScript / JavaScript | `src/lsp/ts_js/` | [ts-morph](https://ts-morph.com/) + Bun + [Hono](https://hono.dev/) | `9001` |

---

## How to run them

### As Make targets

```bash
make install-lsp        # Python + TS/JS deps
make run-lsp            # both drivers in parallel
make run-lsp-python     # Python only
make run-lsp-ts         # TS/JS only
```

Each driver prints `READY port=<n>` on stdout once it's listening. Override the port inline:

```bash
make run-lsp-python LSP_PY_PORT=9500
make run-lsp-ts     LSP_TS_PORT=9600
```

### Telling the backend where the drivers live

The backend can run drivers **in-process** (Python, today) or as **out-of-process JSON-RPC services**. To use out-of-process drivers, set the URL in `src/backend/.env`:

```ini
VNOC_LSP_PYTHON_URL=http://127.0.0.1:9002
VNOC_LSP_TS_JS_URL=http://127.0.0.1:9001
```

The endpoint path is always `/rpc` on each driver.

### Running a driver standalone

Each driver is a normal process you can spawn yourself — useful when developing.

**Python:**

```bash
.venv/bin/python -m vnoc_lsp_python --port 9002
# defaults: --host 127.0.0.1, --port 9002 (0 = auto-pick a free port)
```

**TS/JS (Bun):**

```bash
cd src/lsp/ts_js
bun run start -- --host 127.0.0.1 --port 9001
```

---

## The driver protocol

Every driver implements the same JSON-RPC methods, defined as Pydantic models in `src/backend/app/core/parser/drivers/protocol.py`:

| Method | Params | Result |
|---|---|---|
| `initialize` | `project_path`, `language`, `config` | `status`, supported `extensions` |
| `parse_file` | `file_path`, `content`, `resolve_mro` | `ParseResult` — list of `BaseNode`, plus the (possibly ID-injected) `content` and a `modified` flag |
| `resolve_calls` | `file_path`, `calls: BaseNode[]` | `CallFrameResult` — resolved `CallFrameStack` |
| `read_or_inject_file` | `file_path` | `FileIdResult` — `file_id`, `modified` |
| `read_or_inject_folder` | `folder_path` | `FolderIdResult` — `folder_id`, `modified` |
| `shutdown` | — | `status` |

The Pydantic protocol class `LanguageDriver` (also in `protocol.py`) is the **single source of truth**; both the in-process `LocalPythonDriver` and the out-of-process JSON-RPC clients implement it.

### Where the backend invokes it

- `src/backend/app/core/parser/drivers/manager.py` — picks the right driver per file/language.
- `src/backend/app/core/parser/drivers/json_rpc_client.py` — wire protocol against a driver URL.
- `src/backend/app/core/parser/drivers/local_python.py` — in-process Python driver (default when no `VNOC_LSP_PYTHON_URL` is set).
- `src/backend/app/core/parser/graph_builder/orchestrator.py` — calls the driver during project ingest and watcher re-parses.

---

## Adding a new language

Walking the floor for a hypothetical Go driver:

1. **Create the driver process** (`src/lsp/go/`) implementing the six JSON-RPC methods listed above. Return AST nodes that match the shared `BaseNode` shape (see `src/backend/app/core/parser/ast/models.py`).
2. **Inject stable IDs** in `read_or_inject_file` / `read_or_inject_folder`. The Python driver writes `""" ID: <uuid> """` as the function docstring; pick a comment form that's natural for your language and stable across formatters. See `06-function-class-tracking.md`.
3. **Register the driver** in `src/backend/app/core/parser/drivers/manager.py` so files with the right extensions route to it.
4. **Add a Make target** mirroring `run-lsp-python` / `run-lsp-ts` (port + install command).
5. **Expose its URL** in `.env.example` (e.g. `VNOC_LSP_GO_URL=http://127.0.0.1:9003`).

---

## Choosing in-process vs out-of-process

| | In-process | Out-of-process JSON-RPC |
|---|---|---|
| Setup | Zero — backend imports the driver | Run a separate process |
| Crash isolation | Driver crash takes the backend down | Driver crash is contained |
| Languages | Only Python (today) | Any language |
| Latency | Best (function call) | Localhost RPC overhead |
| Recommended for | Quick local dev | Production, non-Python languages, driver development |

Python defaults to in-process. Set `VNOC_LSP_PYTHON_URL` to flip it.

---

## Ports cheat-sheet

| Variable | Default | Service |
|---|---|---|
| `LSP_PY_PORT` | `9002` | Python driver |
| `LSP_TS_PORT` | `9001` | TS/JS driver |

All driver URLs are `http://<host>:<port>/rpc`.

Next: [06 · Function & Class Tracking](06-function-class-tracking.md).

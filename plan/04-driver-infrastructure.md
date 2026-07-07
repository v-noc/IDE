# Driver Infrastructure: Setup, Routing & Multi-Language

How to structure `src/lsp/`, run multiple language drivers, and connect them to the backend.

---

## Architecture Options Considered

### Option A: One Port Per Driver (Backend Routes)

```
Backend (DriverManager)
  ├──► http://localhost:9100/rpc  →  Python Driver
  └──► http://localhost:9200/rpc  →  JS/TS Driver
```

The backend's `DriverManager` maps file extensions to driver URLs. Each driver is a
standalone process on its own port. The backend does the routing — no extra gateway.

- **Pros:** Simple. Isolated. Each driver is independently debuggable (curl it).
  One driver crashing doesn't take down others. Easy to add new languages.
- **Cons:** Port management. Multiple HTTP connections.

### Option B: Single Gateway Server

```
Backend
  └──► http://localhost:9000/rpc  →  Gateway/Router
                                       ├──► Python Driver (subprocess/in-process)
                                       └──► JS/TS Driver (subprocess/in-process)
```

One gateway process receives all requests and dispatches by language.

- **Pros:** Single endpoint for the backend. Centralized logging.
- **Cons:** Extra hop. Single point of failure. Gateway is yet another service
  to build and maintain. The backend can already do the routing itself.

### Option C: Stdio Pipes (LSP Style)

```
Backend
  ├──► stdin/stdout  →  Python Driver (child process)
  └──► stdin/stdout  →  JS/TS Driver (child process)
```

No HTTP at all. Communicate over stdin/stdout with JSON-RPC framing.

- **Pros:** No port management. Tighter lifecycle control (parent kills child).
- **Cons:** Can't test driver independently (no curl). Harder to debug.
  Can't share a driver across multiple backend instances. No batch HTTP.

### Chosen: Option A — One Port Per Driver

Option A wins because:

1. The backend **already needs a DriverManager** to know which driver handles which extension.
   Adding "route to the right port" is trivial — no gateway needed.
2. Each driver is **fully standalone** — start it, curl it, test it in isolation.
3. Debugging is straightforward: point any HTTP tool at the driver port.
4. In Docker, each driver becomes its own service with a named network alias.
   No port conflicts. The backend resolves by service name.
5. Adding a language = adding a container + one registry entry. Zero backend code changes.

---

## Directory Structure: `src/lsp/`

```
src/lsp/
├── python/                     # Python language driver
│   ├── server.py               # HTTP entry point (uvicorn/starlette)
│   ├── handlers.py             # JSON-RPC method → handler dispatch
│   ├── parser.py               # ← from parser/ast/parser.py (parso)
│   ├── id_injector.py          # ← from parser/ast/id_injector.py (libcst)
│   ├── scanner.py              # ← from parser/ast/scanner.py
│   ├── jedi_manager.py         # ← from jedi_adapter/manager.py
│   ├── mro_resolver.py         # ← from jedi_adapter/resolver.py
│   ├── call_resolver.py        # ← from jedi_adapter/call_resolver.py
│   ├── models.py               # Wire types (shared with backend)
│   ├── requirements.txt        # jedi, parso, libcst, pydantic, starlette, uvicorn
│   └── Dockerfile
│
├── js/                         # JS/TS language driver (future)
│   ├── src/
│   │   ├── server.ts           # HTTP entry point (Bun.serve)
│   │   ├── handlers.ts         # JSON-RPC dispatch
│   │   ├── parser.ts           # ts-morph based parser
│   │   ├── id-injector.ts      # JSDoc/comment-based ID injection
│   │   └── models.ts           # Wire types (same schema as Python)
│   ├── package.json            # bun, ts-morph
│   ├── tsconfig.json
│   └── Dockerfile
│
└── shared/                     # Optional: shared protocol artifacts
    ├── protocol.schema.json    # JSON Schema for all RPC types
    └── test-fixtures/          # Golden test files for cross-driver validation
        ├── python/
        │   ├── input.py
        │   └── expected.json
        └── js/
            ├── input.ts
            └── expected.json
```

### Why `src/lsp/` not `src/drivers/`

The directory already exists in the repo. These **are** language servers — they parse,
analyze, and return structured symbol data. `lsp/` is accurate and concise.

---

## How Each Driver Runs

### Python Driver

```bash
# Development
cd src/lsp/python
pip install -r requirements.txt
python server.py --port 9100

# Docker
docker build -t vnoc-lsp-python src/lsp/python
docker run -p 9100:9100 vnoc-lsp-python
```

**`server.py` startup flow:**
1. Parse `--port` arg (default: `0` = auto-assign free port).
2. Start HTTP server on the port.
3. Print `READY port=<PORT>` to stdout (backend reads this).
4. Wait for `initialize` RPC call.

### JS/TS Driver (Future)

```bash
# Development
cd src/lsp/js
bun install
bun run src/server.ts --port 9200

# Docker
docker build -t vnoc-lsp-js src/lsp/js
docker run -p 9200:9200 vnoc-lsp-js
```

Same `READY port=<PORT>` stdout contract. Same JSON-RPC protocol.
Different internals (ts-morph instead of parso/jedi).

---

## How the Backend Connects

### Driver Registry

The backend maintains a static registry mapping languages/extensions to driver config.
This lives in `src/backend/app/core/parser/driver_config.py`:

```python
DRIVER_REGISTRY = {
    "python": {
        "extensions": [".py"],
        "command": ["python", "src/lsp/python/server.py", "--port", "0"],
        # or for docker:
        # "url": "http://lsp-python:9100/rpc",
    },
    "javascript": {
        "extensions": [".js", ".jsx", ".ts", ".tsx"],
        "command": ["bun", "run", "src/lsp/js/src/server.ts", "--port", "0"],
        # or for docker:
        # "url": "http://lsp-js:9200/rpc",
    },
}
```

Two modes:
- **Subprocess mode** (`command`): Backend spawns the driver, reads port from stdout.
  Best for local development.
- **Remote mode** (`url`): Driver is already running (Docker, remote server).
  Backend connects directly. Best for production/Docker.

### DriverManager (Backend)

```python
class DriverManager:
    """
    Manages driver lifecycle and routing.
    This IS the router — no separate gateway needed.
    """

    async def get_driver(self, file_extension: str) -> DriverClient:
        """
        Returns the DriverClient for the given file extension.
        Starts the driver process if not already running.
        """
        language = self._extension_to_language(file_extension)
        if language not in self._active_drivers:
            await self._start_driver(language)
        return self._active_drivers[language]

    async def _start_driver(self, language: str):
        config = DRIVER_REGISTRY[language]

        if "url" in config:
            # Remote mode: driver is already running
            client = DriverClient(config["url"])
        else:
            # Subprocess mode: spawn and wait for READY
            process = subprocess.Popen(
                config["command"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            port = self._read_ready_port(process.stdout)
            client = DriverClient(f"http://localhost:{port}/rpc")

        await client.initialize(self._project_path)
        self._active_drivers[language] = client

    async def shutdown_all(self):
        for client in self._active_drivers.values():
            await client.shutdown()
```

### How Orchestrator Uses It

```python
class GraphBuilderOrchestrator:
    def __init__(self, project_node, uow, driver_manager: DriverManager):
        self.driver_manager = driver_manager
        # ...

    async def _process_file(self, file_path: str, content: str):
        ext = Path(file_path).suffix          # ".py"
        driver = await self.driver_manager.get_driver(ext)
        result = await driver.parse_file(file_path, content, resolve_mro=True)
        # result.nodes, result.content, result.modified — same shape regardless of language
```

The orchestrator doesn't know or care if it's talking to the Python driver or the JS driver.
The protocol is identical.

---

## Port Assignment Strategy

### Local Development (Subprocess Mode)

Each driver auto-assigns a free port:

```python
# Inside driver server.py
import socket

def find_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]

port = args.port if args.port != 0 else find_free_port()
# start server on port
print(f"READY port={port}", flush=True)
```

The backend reads `READY port=<N>` from the subprocess stdout. No hardcoded ports.
No conflicts if multiple projects run simultaneously.

### Docker (Remote Mode)

Each driver has a fixed internal port. Docker maps/exposes as needed:

```yaml
# docker-compose.yml
services:
  lsp-python:
    build: ../../lsp/python
    ports:
      - "9100:9100"
    environment:
      - PORT=9100

  lsp-js:
    build: ../../lsp/js
    ports:
      - "9200:9200"
    environment:
      - PORT=9200

  backend:
    build: .
    environment:
      - LSP_PYTHON_URL=http://lsp-python:9100/rpc
      - LSP_JS_URL=http://lsp-js:9200/rpc
    depends_on:
      - lsp-python
```

The backend reads URLs from environment variables. No subprocess spawning in Docker.

---

## Request Routing Flow

```
File changed: src/app/utils.py
    │
    ▼
FileScanner detects change
    │
    ▼
DriverManager.get_driver(".py")
    │
    ├─ Is Python driver running? ─── No ──► start subprocess / connect to URL
    │                                             │
    │                                             ▼
    │                                        READY port=9100
    │                                             │
    ├───────────────────◄─────────────────────────┘
    │
    ▼
DriverClient("http://localhost:9100/rpc")
    │
    ├──► parse_file(path, content, resolve_mro=True)
    │        → returns nodes, modified content
    │
    ├──► resolve_calls(path, calls)       (Phase 2)
    │        → returns call_frame_stack
    │
    ▼
Backend stores in DB (same model for all languages)
```

For a mixed-language project (future):

```
File changed: src/app/utils.py     → DriverManager.get_driver(".py")  → Python driver
File changed: src/app/helpers.ts   → DriverManager.get_driver(".ts")  → JS/TS driver
                                                                          │
Both return the same shape: nodes with name, qname, position, type        │
                                                                          ▼
                                                          Same DB model, same graph
```

---

## Health Checking & Recovery

Each `DriverClient` should handle transient failures:

```python
class DriverClient:
    async def _call(self, method: str, params: dict) -> dict:
        for attempt in range(3):
            try:
                response = await self.http.post(self.url, json={...})
                return self._parse_response(response)
            except (ConnectionError, TimeoutError):
                if attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
```

If a driver process dies (subprocess mode), `DriverManager` detects it on the next
request and restarts:

```python
async def get_driver(self, ext: str) -> DriverClient:
    language = self._extension_to_language(ext)
    client = self._active_drivers.get(language)

    if client and not await client.is_alive():
        del self._active_drivers[language]
        client = None

    if client is None:
        await self._start_driver(language)

    return self._active_drivers[language]
```

---

## Adding a New Language (The Whole Point)

To add support for a new language (e.g., Go, Rust):

1. **Create `src/lsp/<language>/`** with a server implementing the 6 JSON-RPC methods
   from `02-driver-protocol.md`.

2. **Add to registry:**
   ```python
   DRIVER_REGISTRY["go"] = {
       "extensions": [".go"],
       "command": ["./src/lsp/go/server", "--port", "0"],
   }
   ```

3. **Update `FileScanner`** to include the new extensions.

4. **Done.** No other backend changes. The protocol handles everything.

The only contract is: your driver speaks JSON-RPC 2.0, implements the 6 methods,
and returns symbols in the shared shape (`name`, `qname`, `position`, `type`, `children`).

---

## Summary

| Question | Answer |
|----------|--------|
| Separate port per driver? | **Yes.** Each driver is its own HTTP server on its own port. |
| Single router/gateway? | **No.** The backend's `DriverManager` is the router. No extra service. |
| How are ports assigned? | **Auto** in dev (driver picks free port, reports via stdout). **Fixed** in Docker (env vars). |
| How does the backend know which driver to use? | **Extension → language → driver** mapping in `DRIVER_REGISTRY`. |
| What if a driver crashes? | `DriverManager` detects on next request, restarts the subprocess. |
| How to add a new language? | Create `src/lsp/<lang>/`, add to registry, update `FileScanner` extensions. |

# Migration Plan: Step-by-Step

Each phase produces a working system. Test after each phase to verify identical output.

---

## Phase 0: Preparation

**Goal:** Clean up dead code and establish the test baseline.

### Steps

1. **Delete `parser/ast/visitor.py`** — broken stub, not imported anywhere.

2. **Create a snapshot test** for the current parser:
   - Pick 2-3 representative Python files from a test project.
   - Run the full `resync()` pipeline.
   - Dump the resulting DB state (files, classes, functions, calls with their qnames and positions).
   - Save as a JSON fixture — this is the **golden output** you compare against after each phase.

3. **Document current `resync()` timing** on the test project (rough baseline for
   performance regression checks).

### Files touched
```
DELETE  parser/ast/visitor.py
CREATE  tests/migration/test_parser_snapshot.py   (or similar)
CREATE  tests/migration/fixtures/golden_output.json
```

---

## Phase 1: Define the Driver Interface (Backend Side)

**Goal:** Create the abstraction layer that the backend will program against.
No behavior change yet — the "local" implementation calls existing code directly.

### Steps

1. **Create `parser/driver_protocol.py`** — Python Protocol (abstract interface):

   ```python
   from typing import Protocol, List, Optional
   from parser.ast.models import BaseNode, CallNode

   class LanguageDriver(Protocol):
       async def initialize(self, project_path: str, config: dict = {}) -> dict: ...
       async def parse_file(self, file_path: str, content: str, resolve_mro: bool = False) -> ParseResult: ...
       async def resolve_calls(self, file_path: str, calls: List[CallNode]) -> CallFrameResult: ...
       async def read_or_inject_file_id(self, file_path: str) -> FileIdResult: ...
       async def read_or_inject_folder_id(self, folder_path: str) -> FolderIdResult: ...
       async def shutdown(self) -> None: ...
   ```

   Plus dataclasses for `ParseResult`, `CallFrameResult`, `FileIdResult`, `FolderIdResult`.

2. **Create `parser/driver_local.py`** — Local (in-process) implementation:
   - Implements `LanguageDriver` by calling the existing code directly.
   - `parse_file` → calls `scan()` + optionally `MROResolver` inline.
   - `resolve_calls` → calls `CallHierarchyResolver` inline.
   - `read_or_inject_file_id` → calls `FileTracker.process_file()`.
   - `read_or_inject_folder_id` → calls `FolderTracker.process_folder()`.
   - This is a **shim** — proves the interface works without changing any behavior.

3. **Verify:** Run the snapshot test. Output must be identical to Phase 0 golden output.

### Files touched
```
CREATE  parser/driver_protocol.py
CREATE  parser/driver_local.py
```

---

## Phase 2: Rewire the Backend to Use the Driver Interface

**Goal:** All backend modules call `LanguageDriver` methods instead of importing
parser internals directly. Still using the local (in-process) implementation.

### Steps

1. **Update `orchestrator.py`:**
   - Remove `from app.core.parser.jedi_adapter.manager import JediProjectManager`.
   - Accept a `LanguageDriver` in constructor (default: `LocalDriver`).
   - Pass driver to `Collector`, `PhaseProcessor`, etc.

2. **Update `collector.py`:**
   - Remove `from app.core.parser.ast.scanner import scan`.
   - Remove `from app.core.parser.jedi_adapter.resolver import MROResolver`.
   - Remove `from app.core.parser.jedi_adapter.manager import JediProjectManager`.
   - `process_file()`: call `driver.parse_file(file_path, content, resolve_mro=True)`
     instead of `scan()` + passing `MROResolver` to `ASTProcessor`.

3. **Update `ast_processor.py`:**
   - Remove `MROResolver` from constructor and `_resolve_mro` method.
   - MRO data now comes pre-resolved in the `parse_file` response.
   - `_flatten_nodes`: read `base_classes` from the AST node (driver already populated it)
     instead of calling `self._resolve_mro()`.
   - This simplifies `ASTProcessor` significantly.

4. **Update `body_parser.py`:**
   - Remove `from app.core.parser.ast.scanner import scan`.
   - `process_ast()`: call `driver.parse_file()` instead of `scan()`.
   - Pass driver to `CallChainBuilder`.

5. **Update `call_graph/builder.py`:**
   - Remove `from app.core.parser.jedi_adapter.call_resolver.call_resolver import ...`.
   - Remove `from app.core.parser.jedi_adapter.manager import JediProjectManager`.
   - `resolve_call_hierarchy()`: call `driver.resolve_calls(file_path, calls)` instead of
     creating `CallHierarchyResolver` and calling it.
   - Merge + diff logic stays unchanged.

6. **Update `discovery/file_tracker.py`:**
   - Remove `import libcst`, remove `from app.core.parser.ast.id_injector import ...`.
   - `process_file()`: call `driver.read_or_inject_file_id(file_path)`.

7. **Update `discovery/folder_tracker.py`:**
   - Same pattern as file_tracker.

8. **Update `graph_builder/utils/phase_processor.py`:**
   - Remove `JediProjectManager` from constructor.
   - Accept `LanguageDriver` and pass it through.

9. **Verify:** Snapshot test. Identical output.

### Files modified
```
MODIFY  parser/graph_builder/orchestrator.py
MODIFY  parser/graph_builder/collection/collector.py
MODIFY  parser/graph_builder/collection/ast_processor.py
MODIFY  parser/graph_builder/analysis/body_parser.py
MODIFY  parser/graph_builder/call_graph/builder.py
MODIFY  parser/graph_builder/discovery/file_tracker.py
MODIFY  parser/graph_builder/discovery/folder_tracker.py
MODIFY  parser/graph_builder/utils/phase_processor.py
```

### Key principle
After this phase, **no file in `graph_builder/`** imports from `parser/ast/` or
`parser/jedi_adapter/` directly. All language-specific access goes through the
`LanguageDriver` interface.

---

## Phase 3: Build the Python Driver (Separate Process)

**Goal:** Package the Python-specific code as a standalone HTTP server with JSON-RPC.

### Directory Structure

```
src/drivers/python/
├── server.py              # HTTP server + JSON-RPC dispatcher
├── handlers.py            # Method handler implementations
├── parser.py              # ← moved from parser/ast/parser.py
├── id_injector.py         # ← moved from parser/ast/id_injector.py
├── scanner.py             # ← moved from parser/ast/scanner.py
├── jedi_manager.py        # ← moved from jedi_adapter/manager.py
├── mro_resolver.py        # ← moved from jedi_adapter/resolver.py
├── call_resolver.py       # ← moved from jedi_adapter/call_resolver/call_resolver.py
├── models.py              # Shared types (copy of ast/models.py + CallFrameStack)
├── requirements.txt       # jedi, parso, libcst, pydantic, uvicorn/starlette
└── Dockerfile             # (optional) for containerized deployment
```

### Steps

1. **Create `src/drivers/python/` directory.**

2. **Copy (not move yet) the parser files** into the driver directory:
   - `parser.py`, `id_injector.py`, `scanner.py` from `parser/ast/`
   - `manager.py` → `jedi_manager.py` from `jedi_adapter/`
   - `resolver.py` → `mro_resolver.py` from `jedi_adapter/`
   - `call_resolver.py` from `jedi_adapter/call_resolver/`
   - `models.py` from `parser/ast/` (copy, both sides need it)

3. **Fix imports** in the copied files — they no longer live inside the `app` package.
   Replace `from app.core.parser.xxx import ...` with local imports.

4. **Create `server.py`:**
   - Lightweight HTTP server (e.g., `starlette` or plain `http.server`).
   - Single `POST /rpc` endpoint.
   - JSON-RPC 2.0 dispatcher that routes `method` to handler functions.
   - On startup: print `READY port=<PORT>` to stdout.

5. **Create `handlers.py`:**
   - `handle_initialize(params)` → creates `JediProjectManager`.
   - `handle_parse_file(params)` → calls `scan()` + optionally `MROResolver`.
   - `handle_resolve_calls(params)` → calls `CallHierarchyResolver`.
   - `handle_read_or_inject_file_id(params)` → calls `FileTracker` logic.
   - `handle_read_or_inject_folder_id(params)` → calls `FolderTracker` logic.
   - `handle_shutdown(params)` → graceful exit.

6. **Create `requirements.txt`:**
   ```
   jedi
   parso
   libcst
   pydantic
   uvicorn
   starlette
   ```

7. **Test the driver standalone:**
   - Start the server: `python server.py --port 9100`
   - Send JSON-RPC requests with curl/httpie.
   - Verify responses match expected format from `02-driver-protocol.md`.

### Files created
```
CREATE  src/drivers/python/server.py
CREATE  src/drivers/python/handlers.py
CREATE  src/drivers/python/parser.py
CREATE  src/drivers/python/id_injector.py
CREATE  src/drivers/python/scanner.py
CREATE  src/drivers/python/jedi_manager.py
CREATE  src/drivers/python/mro_resolver.py
CREATE  src/drivers/python/call_resolver.py
CREATE  src/drivers/python/models.py
CREATE  src/drivers/python/requirements.txt
```

---

## Phase 4: Create the Remote Driver Client

**Goal:** Build the JSON-RPC HTTP client that replaces the local driver.

### Steps

1. **Create `parser/driver_client.py`:**
   - Implements the same `LanguageDriver` protocol.
   - Each method serializes params to JSON-RPC, sends HTTP POST, deserializes response.
   - Uses `httpx` (async HTTP client) for non-blocking requests.
   - Handles JSON-RPC error responses → raises appropriate exceptions.
   - Supports batch requests (send list of JSON-RPC calls).

2. **Create `parser/driver_manager.py`:**
   - `DriverManager.start_driver(language, project_path)`:
     - Spawns driver subprocess (e.g., `python src/drivers/python/server.py`).
     - Reads `READY port=<PORT>` from stdout.
     - Creates `DriverClient(port)`.
     - Sends `initialize(project_path)`.
     - Returns the client.
   - `DriverManager.stop_driver(language)`:
     - Sends `shutdown`.
     - Terminates subprocess.
   - Health check: periodic ping or process alive check.

3. **Update `orchestrator.py`:**
   - Use `DriverManager` to start/get the Python driver.
   - Pass the `DriverClient` as the `LanguageDriver` implementation.

4. **Verify:** Snapshot test with the remote driver. Identical output.

### Files created/modified
```
CREATE  parser/driver_client.py
CREATE  parser/driver_manager.py
MODIFY  parser/graph_builder/orchestrator.py  (switch from LocalDriver to DriverClient)
```

---

## Phase 5: Cleanup

**Goal:** Remove dead code from the backend. Trim backend dependencies.

### Steps

1. **Delete `parser/ast/parser.py`** — code now lives in driver.
2. **Delete `parser/ast/id_injector.py`** — code now lives in driver.
3. **Delete `parser/ast/scanner.py`** — code now lives in driver.
4. **Delete `parser/jedi_adapter/`** — entire directory, code now lives in driver.
5. **Delete `parser/driver_local.py`** — no longer needed (was the migration shim).
6. **Keep `parser/ast/models.py`** — shared protocol types, still used by backend.
7. **Remove from backend `requirements.txt`:** `jedi`, `parso`, `libcst`.
8. **Add to backend `requirements.txt`:** `httpx` (if not already present).
9. **Update `parser/ast/__init__.py`** — only re-export models.

### Files touched
```
DELETE  parser/ast/parser.py
DELETE  parser/ast/id_injector.py
DELETE  parser/ast/scanner.py
DELETE  parser/ast/visitor.py          (if not already deleted in Phase 0)
DELETE  parser/jedi_adapter/           (entire directory)
DELETE  parser/driver_local.py
MODIFY  parser/ast/__init__.py
MODIFY  requirements.txt              (backend)
```

---

## Phase Summary

| Phase | What | Risk | Rollback |
|-------|------|------|----------|
| 0 | Clean dead code, create test baseline | None | Git revert |
| 1 | Create driver interface + local shim | Low — no behavior change | Delete new files |
| 2 | Rewire backend to use interface | Medium — many files change | Git revert to Phase 1 |
| 3 | Build standalone Python driver | Low — additive, no backend changes | Delete driver directory |
| 4 | Switch to remote driver client | Medium — introduces HTTP boundary | Switch back to local driver |
| 5 | Delete old code | Low — just cleanup | Git revert (code is in history) |

---

## Testing Strategy

After **each** phase:

1. Run the snapshot test from Phase 0.
2. Compare DB output (files, classes, functions, calls) against golden fixture.
3. Diff should be empty.

For Phase 3 specifically:
- Test the driver in isolation (curl → JSON-RPC → verify response shapes).
- Test each method independently before integration.

For Phase 4:
- Test with driver running locally first.
- Add a timeout/retry to `DriverClient` for robustness.

---

## Estimated Effort per Phase

| Phase | Estimated Effort | Dependencies |
|-------|-----------------|--------------|
| 0 | ~1 hour | None |
| 1 | ~2-3 hours | Phase 0 |
| 2 | ~4-6 hours | Phase 1 |
| 3 | ~3-4 hours | Phase 1 (can parallel with Phase 2) |
| 4 | ~2-3 hours | Phase 2 + Phase 3 |
| 5 | ~1 hour | Phase 4 |

**Total: ~13-18 hours** (spread across multiple sessions)

Note: Phases 2 and 3 can be worked on in parallel since they don't touch the same files.
Phase 2 rewires the backend against the interface. Phase 3 builds the driver behind
the same interface.

---

## File Extension Support (Future — Not This Migration)

After this migration is complete, adding JS/TS support requires:

1. Build `src/drivers/js/` (Bun + ts-morph) implementing the same JSON-RPC protocol.
2. Update `FileScanner` to scan `.ts`, `.tsx`, `.js`, `.jsx` files.
3. Register the JS driver in `DriverManager`.
4. No other backend changes needed — the protocol is the same.

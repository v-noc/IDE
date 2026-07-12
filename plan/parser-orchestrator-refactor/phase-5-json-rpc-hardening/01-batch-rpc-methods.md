# Phase 5 / Step 1 — Batch & read-only RPC methods

Files: `app/core/parser/drivers/protocol.py`, `json_rpc_client.py`,
`local_python.py`, `src/lsp/py/vnoc_lsp_python/rpc.py` + `service.py`,
`src/lsp/ts_js/src/jsonrpc.ts` + driver.

## New methods (top)

### `read_file_ids` / `read_folder_ids` — read-only, batched

```jsonc
// request
{ "method": "read_file_ids", "params": { "paths": ["/a.py", "/b.py"] } }
// result
{ "ids": { "/a.py": "FileSchema/…", "/b.py": null } }   // null = no id present
```

- **Never writes.** This is the detection-path call (Phase 3 ladder). The existing
  `read_or_inject_file_id` reads the file and injects an id if missing
  (id_injector side effect) — using it during change detection is what mutates user
  files on a read pass and can re-trigger the watcher.
- Driver impl: same read logic minus the inject branch; py: `file_folder_ids.py`
  already separates read from inject internally — expose the read half.

### `read_or_inject_file_ids` / `read_or_inject_folder_ids` — write, batched

```jsonc
{ "params": { "paths": [...] } }
→ { "results": { path: { "file_id": "...", "modified": true } } }
```

- Used only for **new** files/folders (ladder step 4) and initial project import.
- Driver processes sequentially or with its own small pool; one HTTP round-trip
  replaces N (initial import of 2k files: 2k requests → ⌈2k/500⌉).
- Cap `paths` per request (500) — client chunks; keeps request bodies and driver
  memory bounded.

### `parse_files` — batched window parse (optional, measure first)

```jsonc
{ "params": { "files": [{ "path": "...", "content": "...", "resolve_mro": true }] } }
→ { "results": [ ParseResult... ] }   // order-preserving; per-file error objects inline
```

- Phase 3 windows currently issue `window_size` concurrent `parse_file` calls; HTTP
  overhead per call is ~ms — only worth batching if metrics (client hooks, step 02)
  show it. Spec it now, implement behind driver capability flag.
- Per-file failures must not fail the batch: result slot carries
  `{ "error": { code, message } }`.

### `initialize` gains capabilities

```jsonc
→ { "status": "ok", "extensions": [".py"], "capabilities": ["read_file_ids", "parse_files"],
    "protocol_version": 2 }
```

Backend behavior: if a capability is missing (older driver), fall back to per-file
methods — `DriverManager` stores the capability set per driver; call sites ask
`driver.supports("read_file_ids")`. Keeps py/ts drivers independently deployable.

## Protocol module changes (middle)

- Add params/result models to `protocol.py` (`ReadFileIdsParams`, `FileIdsResult`, …)
  mirroring existing pydantic style.
- `LanguageDriver` Protocol gains the batch methods with default single-path fallbacks
  implemented in a small `BatchFallbackMixin` so `LocalPythonDriver` works unchanged
  day one.
- Wire format for symbols unchanged (`parse_symbol_list`).

## Server-side notes

- py (`rpc.py`): new `@entry.method()`s calling batched service functions; the service
  loops internally — no per-item threadpool dispatch (one `run_in_threadpool` for the
  whole batch; see step 03 for pool bounds).
- ts_js (`jsonrpc.ts`): mirror; ts driver already builds a ts-morph project — batch id
  reads are just fs reads of headers/jsdoc (`fileFolderIds.ts`).

## Steps (bottom)

1. Spec models in `protocol.py` + capability negotiation in `initialize`.
2. py driver: read-only variants + batch endpoints + capability list.
3. ts_js driver: same.
4. Client methods + chunking (500/request).
5. Switch Phase 3 id ladder to `read_file_ids` (read-only) and new-file path to
   batched inject; delete detection-path per-file calls.
6. Golden tests (Phase 3) still green; add wire-level tests with a recorded
   request/response fixture per method.

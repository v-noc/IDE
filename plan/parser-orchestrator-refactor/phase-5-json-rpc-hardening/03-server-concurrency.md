# Phase 5 / Step 3 — Driver server concurrency & safety

Files: `src/lsp/py/vnoc_lsp_python/` (rpc.py, service.py, jedi_manager.py, server.py),
`src/lsp/ts_js/src/` (jsonrpc.ts, driver/*)

## Python driver (top)

### Problem

Every RPC method is `run_in_threadpool(service.X)` (rpc.py:48-83) with the default
AnyIO pool (40 threads) and **no serialization around shared state**: one
`PythonDriverService` holds one jedi project / parso cache; the backend fires up to 50
concurrent calls (detector `max_concurrency=50`, window parse). jedi's `Project`/
`Script` objects and parso's default cache are not designed for unsynchronized
concurrent mutation — today this "mostly works" and occasionally corrupts state or
races the id-injector's file writes.

### Fix: explicit worker model

```
rpc method → asyncio.Queue → K worker threads (K = min(cpu, 4), setting)
             each worker owns its OWN jedi environment/parso cache slice
             file-id injection serialized per path (path-keyed asyncio.Lock)
```

- Simplest correct version first: `K=1` worker + queue (matches the implicit
  assumption the code already makes; measure — parse is CPU-bound Python, GIL caps
  gains anyway). Bump K only with per-worker jedi state.
- Bound the queue (e.g. 256); when full, JSON-RPC returns a busy error → client
  backoff (step 02) absorbs it.
- `read_file_ids` (read-only, no jedi) can bypass the queue — pure fs reads.

### Injection safety

- Path-keyed lock around read-modify-write of source files (`id_injector.py`) —
  two concurrent inject calls for the same file currently race (lost write).
- Write via temp-file + `os.replace` (atomic) so a killed driver never leaves a
  truncated source file. **This touches user code — highest-care change in the phase.**
- After Phase 3/5 the detection path never injects; injection happens for new files
  only, further shrinking the race window.

### Lifecycle

- `/health`: returns project path + queue depth + worker liveness.
- `shutdown`: drain queue (with deadline), then exit — today it returns `{"ok"}`
  and does nothing (rpc.py:85-89).
- `server.py`: handle SIGTERM the same way (uvicorn hooks).

## ts_js driver (middle)

- Bun/Hono is single-threaded event loop — no thread races, but `parse_file` on a huge
  file blocks the loop and stalls every in-flight request: chunk long-running ts-morph
  work with `await Bun.sleep(0)` yield points, or move parse into a `Worker`
  (bun worker_threads) with the same queue-of-K pattern for symmetry.
- Mirror `/health` + graceful shutdown + busy error.
- `createMorphProject` caching: verify project instance reuse across requests is
  intentional and memory-bounded (ts-morph keeps source files in memory — evict files
  not touched in N minutes, or rebuild project per sync session via an explicit
  `begin_session/end_session` RPC pair if metrics show growth).

## Backend `api/json_rpc` server (small)

- Entrypoint middleware (`logging_middleware`, entrypoint.py:21) logs full raw
  request/response at INFO — log bodies truncated (first 500 bytes) at DEBUG; INFO gets
  method + id + duration only. Log payloads can be large (batched logs).

## Steps (bottom)

1. py: queue + single worker + path locks + atomic writes; K configurable.
2. py: health + real shutdown + SIGTERM.
3. ts_js: health + busy error + yield-points (worker only if metrics demand).
4. ts_js: memory bound for the morph project cache.
5. Load test: 4 concurrent syncs of the sample project against one driver —
   zero corrupted files (hash-verify sources after), zero 500s, bounded RSS.
6. Backend middleware log truncation.

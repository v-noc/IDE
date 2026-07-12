# Phase 5 / Step 2 — Client resilience

File: `app/core/parser/drivers/json_rpc_client.py` (+ `manager.py`)

## Failure taxonomy → policy (top)

| Failure | Today | Policy after |
|---|---|---|
| connect refused / timeout | exception → file skipped or sync dies | retry 3× exp backoff (0.2s→2s, jitter); then `DriverError` + mark driver unhealthy |
| HTTP 5xx | same | same retry policy |
| JSON-RPC error `-32603` (internal) | `DriverRpcError` | retry once (drivers are stateless per call except project index); then raise |
| JSON-RPC method error (invalid params, parse error in file) | `DriverRpcError` | NO retry — deterministic; wrap `DriverError(file=...)`, per-file isolation handles it |
| response not JSON / truncated | `r.json()` raises ValueError uncaught (json_rpc_client.py:103) | treat as transport failure → retry path |
| driver process dead | `is_alive()` lies (checks local httpx object only, line 176) | health check + supervisor (below) |

Retries are safe: all driver methods are idempotent (`read_*` pure;
`read_or_inject_*` converges — second inject finds the id; `parse_file` pure given
content; `resolve_calls` pure).

## Health & supervision (middle)

```
DriverManager (manager.py)
├── health(): GET {base}/health  (drivers add the route; 200 + {"status","project"})
├── ensure_healthy(driver):
│      unhealthy → recreate client → initialize(project) → replay capability set
└── call wrapper: on DriverError(unhealthy) → ensure_healthy → single re-attempt
```

- `is_alive()` implements a real check (health with 2 s timeout); keep the cheap local
  check as fast path.
- Warmup (`warmup_drivers`, manager.py:50) uses health first — a resync against a dead
  ts_js driver currently throws deep inside detection; after: fails fast with a clear
  "driver ts_js unreachable at $URL" `DriverError` before any DB work.

## Transport hygiene

- Per-method timeouts: `parse_file(s)` 120 s (big files), `read_file_ids` 10 s,
  `resolve_calls` 60 s, `initialize` 30 s — dict in one place, overridable via settings.
- Payload: gzip request bodies > 64 KB (httpx `content=gzip.compress(...)`,
  `Content-Encoding: gzip`; both fastapi-jsonrpc and Hono/Bun handle it — verify ts_js,
  else add middleware there).
- Connection pool limits on the httpx client (currently default-unbounded,
  json_rpc_client.py:56): `max_connections = parse_concurrency + small headroom`.
- Keep single shared `AsyncClient` per driver (already the case), add `aclose` on
  manager shutdown (exists, manager.py:118).

## Metrics hooks

Lightweight counter/timer on `_call`: `{method, driver, ok/err, ms, req_bytes,
resp_bytes}` — pushed into `performance.tracker` spans so Phase 3's RPC-count budget
test and future dashboards read one source. This also settles the "is parse_files
batching worth it" question with data.

## Backend logs RPC (folded in here)

`api/v1/jsonrpc register_logs_batch` (entrypoint.py):

- raise on failure (Phase 4 audit #2) → JSON-RPC error to the SDK,
- cap batch size (reject > N logs with a clear error; SDK chunks),
- write through `SyncWriteBatch` → one commit per RPC batch instead of
  `log_service.create_batch` internals committing per group.

## Steps (bottom)

1. Extract `_call` → `_call_with_policy(method, params, *, timeout, retry)` table-driven.
2. Health routes on both drivers + `DriverManager.ensure_healthy` + honest `is_alive`.
3. Pool limits + gzip + per-method timeouts.
4. Metrics hooks.
5. Logs RPC fixes.
6. Chaos tests: kill driver mid-window (pipeline pauses, supervisor restarts, window
   retries once, sync completes); driver returning 500 on 1 of 100 parses (file
   isolated, 99 synced).

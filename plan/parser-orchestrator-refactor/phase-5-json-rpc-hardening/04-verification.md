# Phase 5 / Step 4 — Verification

## Wire-level protocol tests

Per method (old + new): recorded request/response JSON fixtures asserted against both
drivers (py: pytest + httpx against a spawned uvicorn; ts_js: bun test against Hono).
Capability negotiation: old-driver simulation (capabilities absent) → backend falls
back to per-file methods.

## Read-only guarantee (the watcher-loop killer)

Test: run `read_file_ids` over a tree, then hash every file → **byte-identical**.
Run change detection end-to-end on an unchanged project → zero fs writes
(watch with a recording FS shim or mtime sweep). This invariant is load-bearing for
Phase 6.

## Resilience chaos suite

| Scenario | Expected |
|---|---|
| driver down at sync start | fail fast `DriverError` before any DB write; sync_error emitted |
| driver killed mid-window | supervisor restarts, window retried once, sync completes, 1 commit |
| 1 of 100 files returns parse error | 99 synced; error in sync report |
| driver returns garbage (non-JSON) | retried as transport failure, then isolated |
| queue full (py) / busy (ts) | client backs off and completes; no request lost |
| two concurrent inject calls, same file | file valid, single id, no lost content (hash check) |

## Concurrency/soak

- 4 parallel resyncs (different projects) against one py driver, 10 min soak:
  RSS bounded, no source corruption, latency p95 recorded.
- ts_js: parse 5 MB file while 50 `read_file_ids` in flight → id reads return < 1 s
  (yield-points working).

## Metrics acceptance

`_call` metrics visible in the perf report: per-sync table of
`{method, calls, p50, p95, bytes}`. The Phase 3 RPC-budget test consumes these
counters — one instrumentation, two consumers.

## Backend logs RPC

- SDK batch with DB down → JSON-RPC error (not ok:true); SDK retry path exercised.
- 10k-log batch → rejected with size error; 500-log batch → exactly 1 commit.

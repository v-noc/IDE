# Phase 5 — JSON-RPC Hardening (backend ⇄ language drivers, + logs endpoint)

## Objective

The JSON-RPC seam between the backend and language drivers (`py` in-process/remote,
`ts_js` via Bun) becomes: batched where the pipeline needs it, resilient to transient
failures, bounded on both sides, and honest about health. The backend's own JSON-RPC
surface (`/api/v1/jsonrpc`, log ingestion) gets the same error discipline.

## Scope map (dendrogram)

```
JSON-RPC seam
│
├── protocol (drivers/protocol.py + lsp servers)        01-batch-rpc-methods.md
│   ├── NEW read_or_inject_file_ids(paths[])            ← Phase 3 ladder step 4
│   ├── NEW read_file_ids(paths[])   (read-only, NO injection — detection must
│   │                                  never write; watcher loop killer)
│   ├── NEW parse_files([{path, content?}])  optional streaming window parse
│   └── version/capabilities in initialize result        (backend adapts per driver)
│
├── client (drivers/json_rpc_client.py)                 02-client-resilience.md
│   ├── retries w/ backoff+jitter on connect/5xx/-32603-transient
│   ├── real is_alive() → GET /health on driver
│   ├── per-method timeouts; payload compression (gzip) over threshold
│   └── metrics hooks (count, latency, bytes) per method
│
├── servers                                              03-server-concurrency.md
│   ├── py driver: bounded worker pool (jedi/parso NOT thread-safe under 50 threads),
│   │   /health route, graceful shutdown
│   ├── ts_js driver: mirror batch methods + health (src/lsp/ts_js/src/jsonrpc.ts)
│   └── DriverManager: supervise → restart-on-dead, re-initialize project
│
└── backend logs RPC (api/json_rpc/)                     (small; folded into 02/03)
    └── register_logs_batch honest errors (Phase 4 audit #2), payload cap, and
        batch insert through WriteBatch (one commit per RPC batch)
```

## Non-goals

- No transport change (HTTP stays; unix sockets/stdio measured later if HTTP overhead
  shows up in Phase 3 metrics).
- No new languages.
- No LSP-standard compliance work — this protocol is intentionally narrow.

## Depends on

Phase 3 defines which batch methods are needed and their call sites (id ladder,
window parse). Client resilience (02) has no dependencies and can land first.

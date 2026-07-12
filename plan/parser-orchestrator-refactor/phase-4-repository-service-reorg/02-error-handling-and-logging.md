# Phase 4 / Step 2 — Errors & logging

## The silent-failure audit (fix list)

Ranked by blast radius — each currently converts a failure into wrong data:

1. **`get_by_ids`/`get_all` returning `[]` on exception** (base_repo.py:74-97).
   Downstream `ast_processor._build_existing_map` sees "no existing elements" and
   stages **deletes for the whole file's subtree** on the next diff… except the diff
   also sees nothing, so instead duplicate inserts collide. Either way: raise `DbError`,
   abort the file (isolation policy from Phase 3), never fabricate emptiness.
2. **`entrypoint.register_logs_batch`** (api/json_rpc/entrypoint.py:53-59): exception →
   `print(ex)` → returns `ok=True`. Log producers (vn_logger SDK) believe logs landed.
   Raise the JSON-RPC error; SDK already handles error responses.
3. **`phase_processor._flush_code_element_buffer`** swallow (phase_processor.py:152):
   partial graph "until next sync" with a log nobody reads. Phase 2 flush raises —
   orchestrator marks sync failed, progress shows error (already supported:
   `progress_tracker.set_error`).
4. **`create_nodes` returns `None` on failure** (base_repo.py:49-56): callers like
   `body_parser._flush_inserts` (body_parser.py:67-73) log-and-continue → missing call
   edges. Raise.
5. **`update_document` failures in `update_batch`** (structure_repo.py:146,
   code_element_repo.py:100) return `False`/`None` — collector ignores the return
   (collector.py:91). Gone with Phase 2, listed for the audit trail.
6. **Watcher resync `except Exception: logger.error`** (watcher/service.py:179-185) —
   fine to catch (thread boundary), but must emit `sync_error` **with session id** and
   re-arm cleanly (Phase 6 restructures this).

## Exception hierarchy

`app/utils/exceptions.py`:

```python
class VnocError(Exception):
    def __init__(self, msg, **context):   # context: ids, paths, session_id, method…
        self.context = context

class DbError(VnocError): ...             # wraps DatabaseError/InterfaceError
class NotFoundError(VnocError): ...
class ConflictError(VnocError): ...       # data-version retry exhausted
class DriverError(VnocError): ...         # from DriverRpcError (json_rpc_client.py:27)
class WriteBatchError(DbError): ...       # Phase 2, carries FlushReport
class SyncError(VnocError): ...           # aggregate: failed files, phase, session
```

Boundary translation:

- REST: FastAPI exception handlers in `app/main.py` — `NotFoundError→404`,
  `ConflictError→409`, `DbError/DriverError→502` with safe message, everything logs
  full context server-side.
- JSON-RPC: extend `api/json_rpc/error.py` classes mapping the same way.

## Logging conventions

- `logging.getLogger(__name__)` everywhere (already common); **zero `print(`** in
  `app/` — CI grep gate flips on at the end of this step (~30 sites, half already
  removed by Phases 2–3 deletions).
- Sync-scoped records carry `extra={"session": session_id, "project": project_id}`;
  add a formatter including them (`utils/logging.py` already centralizes config).
- Noise pass: per-file "processing file-->" prints become DEBUG; INFO is per-phase
  summaries (counts, durations from `performance.tracker`); WARNING is recoverable
  skips; ERROR is failed sync/action.
- `performance.tracker.print_report()` (orchestrator.py:243) → log at DEBUG or behind
  `settings.perf_report_enabled`.

## Steps (bottom)

1. Land the exception classes + FastAPI/JSON-RPC handlers (no call-site changes yet).
2. Fix audit items 1, 2, 4 (raising at the source), watching the golden tests.
3. Convert remaining repo/query `except Exception: print` blocks as they migrate in
   step 01 — the executor wraps once, deleting ~25 scattered try/excepts.
4. Logging fields + noise pass.
5. Enable CI grep gates: `print(` in `app/core|app/api|app/db`, `except Exception: pass`.

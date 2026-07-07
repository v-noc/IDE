# Phase 6 / Step 2 — SyncScheduler

New: `app/core/watcher/scheduler.py` (replaces the resync closure in
`watcher/service.py:115-188`)

## State machine per project (top)

```
        notify(ev)                    quiet 0.5s OR age 5s
IDLE ──────────────► DEBOUNCING ─────────────────────────► RUNNING
 ▲                       ▲    (dirty set accumulates)          │
 │                       │                                     │ notify(ev) during run:
 │                       └───────── RUNNING+DIRTY ◄────────────┤   mark dirty, keep going
 │       run done, not dirty                │ run done, dirty  │
 └──────────────────────────────────────────┴── immediate re-DEBOUNCE (short window)
```

```python
class SyncScheduler:
    def __init__(self, resync: Callable[[str, SyncScope], Awaitable[SyncReport]]): ...
    def notify_threadsafe(self, ev: FsEvent): ...          # called via call_soon_threadsafe
    async def request_sync(self, project_id, scope=FULL):  # API route / import entry
    async def shutdown(self): ...                          # drain or cancel, bounded

@dataclass
class DirtyState:
    paths: set[str]            # capped at MAX_TRACKED (e.g. 512)
    overflowed: bool           # cap hit or overflow sentinel → scope = FULL
    first_ts: float; last_ts: float
```

## Rules (middle)

- **Debounce**: run when `now - last_ts ≥ quiet (0.5 s)` **or**
  `now - first_ts ≥ max_wait (5 s)` — fixes the indefinite postponement of the current
  restart-timer (project_watcher.py:34-37). One `asyncio.Task` timer per project.
- **Serialization**: at most one running sync per project (`asyncio.Lock`); different
  projects run independently but under a global semaphore (default 2) so N watched
  projects can't stampede the DB/drivers.
- **Events during run** go into the *next* DirtyState; on completion, if dirty →
  immediately enter DEBOUNCING with the short window. Nothing is ever dropped —
  replaces pause/resume-with-loss.
- **Single entry**: the API resync route and project import call
  `scheduler.request_sync(project_id, FULL)` — no more orchestrator built inside the
  route (`project_routes.py:121`) racing a watcher-built one
  (`ProjectService.resync` from Phase 4 is the shared `resync` callable).
- **Progress/socket**: `sync_started` / `sync_complete` / `sync_error` /
  `project:updated` emitted here, in async context, with session id + scope size —
  the thread-hopping emitter (service.py:51-105) is deleted.
- **Failure**: `SyncError` → `sync_error` event, dirty state *retained*, retry with
  exponential backoff (2 s, 10 s, 60 s cap) instead of today's silent stall until the
  next keystroke.

## WatcherService reshape

`WatcherService` keeps the public surface used by routes
(`start_watching/stop_watching/stop_all`) but becomes thin:

```
WatcherService
├── scheduler: SyncScheduler          (created at app startup with the main loop)
├── watchers: {project_id: ProjectWatcher}
└── start_watching(project) → ProjectWatcher(path, loop, scheduler, id).start()
```

- Singleton via `app.state` only (the `__new__` lock dance, service.py:23-28, goes).
- App lifespan hook: `scheduler.shutdown()` then `stop_all()` on FastAPI shutdown
  (`main.py` lifespan) — today shutdown leaves observer threads running.
- The `self.db` mutation pattern (`set_db`, service.py:42) dissolves: the resync
  callable builds a fresh `ProjectUoW` per run exactly like the current closure
  (service.py:138-146), owned by `ProjectService`.

## Steps (bottom)

1. Implement `SyncScheduler` + `DirtyState` (pure asyncio; unit-testable with a fake
   resync fn and `asyncio` time control).
2. Reshape `WatcherService`; wire lifespan startup/shutdown; delete the resync closure
   and emitter ladder.
3. Route `POST /projects/{id}/resync` through `request_sync` (keep response contract:
   it may now mean "queued" — return `{queued: true, running: bool}`; frontend already
   listens on sockets for completion).
4. Unit tests: debounce windows (quiet, max-wait), coalescing, run+dirty→rerun,
   serialization under concurrent notify, retry backoff, shutdown drain.

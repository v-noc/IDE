# Phase 6 / Step 1 — Event collection & filtering

File: `app/core/watcher/project_watcher.py` (rewrite of `ChangeHandler`)

## Event model (top)

```python
@dataclass(frozen=True)
class FsEvent:
    project_id: str
    path: str                    # absolute
    kind: Literal["created", "modified", "deleted", "moved"]
    dest_path: Optional[str]     # moved only
    ts: float
```

The handler's ONLY job: filter → normalize → hand off to the scheduler. No timers, no
callbacks into sync logic, no blocking.

## Filter chain (order matters — cheapest first)

```
watchdog event
├── 1. event.is_directory and kind == "modified"  → drop
│      (dir-modified fires for every child change; created/deleted/moved dirs pass)
├── 2. extension not in tracked_file_extensions() → drop   (files only;
│      reuse drivers/config.py — same source the scanner uses, scanner.py:42)
├── 3. ignore spec match → drop
│      (reuse FileScanner's pathspec; extract _load_ignore_spec/_is_ignored from
│       scanner.py:46-73,124-128 into watcher-shareable `discovery/ignore_spec.py`;
│       watch the ignore file itself → rebuild spec on change)
├── 4. editor-noise basenames → drop  (*.swp, *.swx, *~, .#*, 4913, *.tmp — configurable)
├── 5. self-write suppression (step 03) → drop
└── 6. loop.call_soon_threadsafe(scheduler.notify, FsEvent(...))
```

- `on_moved` (watchdog `FileMovedEvent` / `DirMovedEvent`) is **not handled today** —
  a move currently surfaces as delete+create with a data-loss window. Add it; carries
  both paths so scoped detection can process it as one move.
- Overflow: watchdog emits `DirDeletedEvent`/queue overflow on huge bursts — map to a
  `kind="overflow"` sentinel with `path=project_root`; scheduler treats it as
  "scope unknown → full resync".

## Thread boundary

Constructor takes the running loop + scheduler:

```python
ProjectWatcher(project_path, loop, scheduler, project_id)
# handler:
self.loop.call_soon_threadsafe(self.scheduler.notify_threadsafe, ev)
```

- `call_soon_threadsafe` is the ONLY loop interaction on the watchdog thread —
  the entire `emit_sync_event` fallback ladder (service.py:51-105) is deleted; socket
  emission happens inside the scheduler's async context naturally.
- Watcher never pauses (`pause/resume` deleted). Suppression (step 03) replaces it:
  events during sync are *wanted* — they schedule the follow-up run.

## Steps (bottom)

1. Extract shared ignore-spec module; wire scanner + watcher to it.
2. Rewrite `ChangeHandler` per filter chain; add `on_moved`; delete debounce Timer
   (debounce moves to the scheduler, step 02).
3. `ProjectWatcher` keeps observer lifecycle (start/stop/is_running) — minus
   pause/resume; keep the existing careful join-avoidance in `stop`
   (project_watcher.py:94-106).
4. Unit tests with synthetic watchdog events: each filter rule; move event; overflow
   sentinel; threadsafe handoff (loop scheduled exactly once per passing event).

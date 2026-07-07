# Phase 6 — Watcher & Sync Scheduling

## Objective

The filesystem watcher becomes an *event source* feeding one central **SyncScheduler**;
it stops being a thread that blocks, drops events, and triggers whole-project rescans.

## Problems today (evidence)

`core/watcher/project_watcher.py` + `core/watcher/service.py`:

1. **Events discard their paths.** `ChangeHandler` callbacks ignore `event.src_path`
   (project_watcher.py:31-53) — any save anywhere triggers a **full** scan + detect
   (every file hashed, every path id-resolved). The event already told us what changed.
2. **No filtering.** Directory events, editor temp files (`.swp`, `~`, `.tmp`),
   untracked extensions, and gitignored paths all trigger resyncs — there is no
   extension/ignore check at the event level, and `event.is_directory` is never
   consulted.
3. **Pause loses events.** During a sync the watch is *unscheduled*
   (`pause_watching`, service.py:130; unschedule = events silently dropped,
   project_watcher.py:109-121). A file saved while a sync runs is **missed until some
   later unrelated event** re-triggers a sync.
4. **Feedback loop half-closed.** Pausing exists to hide the id-injector's writes
   during watcher-triggered syncs — but a resync via the API route
   (`project_routes.py:121`) never pauses the watcher, so injection during a manual
   sync re-triggers a second sync. Phase 5's read-only detection shrinks this, but
   new-file injection still writes.
5. **Debounce is naive.** Fixed 0.5 s timer, cancelled and restarted per event
   (project_watcher.py:34-37) — a long save-burst (git checkout, formatter run over
   the repo) postpones sync indefinitely (no max-wait), then triggers one full rescan.
6. **Threading spaghetti.** watchdog thread → `run_coroutine_threadsafe(...).result(timeout=None)`
   (service.py:150-154) blocks the watchdog callback thread for the whole sync;
   `emit_sync_event` has a 50-line fallback ladder creating event loops
   (service.py:51-105); `WatcherService` is a locked singleton with re-init guards.

## Target architecture (dendrogram)

```
watchdog observer (thread)                     01-event-collection-and-filtering.md
└── ChangeHandler: filter (dir? ext? ignored? self-write?)
    └── loop.call_soon_threadsafe → SyncScheduler.notify(project_id, path, kind)
                                                  ── thread boundary crossed HERE,
                                                     nothing else runs on the thread

SyncScheduler (async, main loop, one per app)  02-sync-scheduler.md
├── per-project DirtyState {paths, kinds, first_event_ts, last_event_ts}
├── debounce: quiet-window 0.5 s AND max-wait 5 s (whichever first)
├── serialized runs per project; events DURING a run accumulate → immediate re-run
├── same entry for watcher, API resync, project import → ProjectService.resync
└── cancellation + shutdown drain

Scoped resync                                   03-scoped-resync-and-self-write-suppression.md
├── orchestrator accepts scope: set[paths] → scan/detect only affected subtrees
├── fallback to full resync when scope unknown (manual button, overflow, renames of dirs)
└── self-write suppression: injector registers (path, content_hash) → scheduler drops
    matching events; watcher never pauses at all
```

## Exit criteria

- Save one file → exactly one scoped sync (~file count 1), one commit; second save
  during the sync → exactly one follow-up sync. Nothing lost, nothing doubled.
- `git checkout` switching 300 files → one sync (max-wait bounded), not 300.
- Editor temp files / gitignored paths → zero syncs.
- Manual resync during watcher activity → single serialized queue, no overlap, no
  injection feedback loop.
- No `asyncio.run`/`run_coroutine_threadsafe(...).result()` in watcher code.

## Depends on

- Phase 3 (pipeline accepts a scope; id resolution no longer writes during detection).
- Phase 4 (`ProjectService.resync` unified entry).
- Phase 5 read-only `read_file_ids` (removes the biggest self-write source).
  01/02 of this phase can land before 3–5 with scope=full (still a big win: filtering,
  no lost events, no thread blocking).

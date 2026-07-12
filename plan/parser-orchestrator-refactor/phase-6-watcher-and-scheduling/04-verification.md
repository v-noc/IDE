# Phase 6 / Step 4 — Verification

## Scheduler unit tests (pure asyncio, fake clock, fake resync fn)

| Case | Expect |
|---|---|
| 1 event | 1 run after quiet window, scope={path} |
| 20 events / 3 s burst on 5 paths | 1 run (max-wait), scope=5 paths |
| event during run | run completes; exactly 1 follow-up run with the new path |
| overflow sentinel | 1 run, scope=FULL |
| resync fn raises | sync_error emitted, dirty retained, backoff retries 2s/10s/60s |
| request_sync while running | queued, no overlap (lock held), served next |
| shutdown during debounce | timer cancelled, no run, clean exit |
| 3 projects notified together | ≤ global semaphore concurrent runs |

## Filter tests (synthetic watchdog events)

- dir-modified dropped; file create/modify/delete/move pass
- `.swp`, `~`, gitignored path, untracked extension → dropped
- ignore-file edit → spec rebuilt (subsequent match honors new rules)
- registered self-write with same hash → dropped; same path, different hash → passes

## E2E with real watchdog (tmp project, real fs)

1. **save one file** → exactly 1 sync, ChangeSet size 1, 1 commit, group edges intact
   (ties Phase 1 invariant to the watcher path).
2. **save during sync** (write while a slow-fixture sync runs) → second sync follows,
   nothing lost — compare final graph to expected.
3. **git checkout** flipping 300 files → ≤ 2 syncs (max-wait windows), final graph
   correct.
4. **new file** (triggers id injection) → 1 sync total; injector write does NOT cause
   a second sync (self-write suppression), file on disk contains id.
5. **API resync spam** (5 rapid POSTs) → serialized, ≤ 2 runs, all 200.
6. **process shutdown** mid-debounce → clean exit, no orphan observer threads
   (assert `threading.enumerate()`).

## Regression watch

- Frontend socket contract: `sync_started/sync_complete/sync_error/project:updated`
  payload shapes unchanged (frontend not touched in this phase).
- Scoped-vs-full equivalence: run scenario 1 with scope forced FULL and with paths
  scope → identical graph dumps.

## Metrics to record here after landing

- keystroke-to-graph-updated latency (save → project:updated): before ___ s → after ___ s
- syncs per minute during active editing session: before ___ → after ___

# Parser / Orchestrator Refactor & Improvement Plan

## Problem

The graph-builder pipeline (`src/backend/app/core/parser/graph_builder/`) works, but it has
four structural problems that get worse as projects grow:

1. **Groups are not transparent to reparse.** A *group* (`StructureGroupSchema`,
   `CodeElementGroupSchema`, `CallGroupSchema`) is a purely graph-level folder-like container —
   it does not exist on disk. The call-graph diff already "jumps" groups
   (`call_graph/diff_calulator.py:_flatten_calls_skipping_groups`), but structure change
   detection (`discovery/change_detector.py`) and code-element sync
   (`collection/ast_processor.py`) compare **physical DB parent vs filesystem parent**.
   Any item a user placed inside a group looks "moved" on the next resync and gets
   re-parented back to its folder/file/class — silently destroying user grouping.
   This is the "detect change here but not there" inconsistency.

2. **Too many commits.** One resync produces a stream of TerminusDB commits (structure
   flush + structure update batch + N code-element chunks + call insert chunks + call
   delete/move chunks + content upserts), and ~49 call sites across repos/services each
   create their own commit. TerminusDB commits are git-style layers: every commit adds a
   layer, and layer count degrades query performance and bloats storage.

3. **Memory and I/O are unbounded.** Every resync: full-document `get_all` of all files and
   folders, one JSON-RPC `read_or_inject_file_id` round-trip per file (even unchanged
   ones), all file contents held in RAM between Phase 1 and Phase 2, and every file parsed
   **twice** (Phase 1 with MRO, Phase 2 without).

4. **Code organization.** `BaseRepo` is a ~450-line god class; error handling is
   `print(exc)` + `return None`; the orchestrator mixes phase logic, progress emission,
   socket events and DB flushing; the JSON-RPC client has no retry/health/batch support.

5. **The watcher amplifies all of the above.** File events discard their paths (every
   save triggers a *full* rescan), the watch is unscheduled during sync so events are
   silently dropped, editor temp files and gitignored paths trigger resyncs, and the
   ID-injector's own writes can re-trigger the watcher (feedback loop — only half-closed
   by pausing, which the API-route resync never does).

## Goal

A group-aware, single-commit-per-sync, memory-bounded pipeline with a clean layering:

- Reparse never disturbs user-created groups (structure, code-element, or call groups).
- One sync ⇒ one logical TerminusDB commit (chunked only for payload limits, clearly
  labeled `part i/n`), plus periodic layer optimization.
- Peak memory is O(window), not O(project).
- Repositories are commit-free primitives; a `SyncWriteBatch` (unit of work) owns commits.
- JSON-RPC drivers get batch endpoints, health checks and retries.
- The watcher feeds a central SyncScheduler: scoped resyncs, no lost events, no
  self-write feedback loops, one serialized sync queue per project.

## Target architecture (dendrogram, top → bottom)

```
watcher (watchdog thread)                    core/watcher/
└── filter (ext/ignore/self-write) → FsEvent
    └── SyncScheduler (async, main loop)
        ├── debounce (quiet 0.5s / max-wait 5s) + coalesce → SyncScope
        ├── serialize per project; re-run if dirtied during sync
        └── request_sync ◄── also: API resync route, project import
            │
            ▼
resync(project, scope)
│
├── 1. SCAN                                  discovery/scanner.py
│   └── walk disk → ScanResult {path→hash, folders}
│
├── 2. SNAPSHOT                              (new) discovery/db_snapshot.py
│   └── lean WOQL query → {id, path, hash, physical_parent} (no full docs)
│       └── GroupResolver: physical parent ──jump groups──► logical parent
│
├── 3. DETECT                                discovery/change_detector.py
│   └── compare by stable ID + logical parent → ChangeSet
│       ├── new / modified / deleted        (hash or path change)
│       └── moved                           (logical parent changed ONLY)
│
├── 4. PLAN                                  collection/*  analysis/*
│   ├── StructurePlan   (folders, files, content)
│   ├── CodeElementPlan (functions, classes; group-aware existing map)
│   └── CallPlan        (call edges; already group-aware)
│
├── 5. EXECUTE                               (new) sync/write_batch.py
│   └── SyncWriteBatch (UoW): accumulate WOQL ops from all plans
│       └── flush → ONE commit  ("sync <id>": chunk part i/n only if payload-bound)
│
└── 6. FINALIZE
    ├── progress complete + project:updated socket event
    └── maintenance: layer count check → TerminusDB optimize/squash
```

## Phases

| Phase | Folder | Theme | Depends on |
|---|---|---|---|
| 1 | `phase-1-group-transparent-reparse/` | Correctness: groups survive resync | — |
| 2 | `phase-2-commit-batching-uow/` | SyncWriteBatch, one commit per sync, commit discipline | — (parallel with 1) |
| 3 | `phase-3-memory-and-pipeline/` | Lean snapshots, ID cache, parse-once, windowed pipeline | 2 |
| 4 | `phase-4-repository-service-reorg/` | Repo split, typed errors, logging, service conventions | 2 |
| 5 | `phase-5-json-rpc-hardening/` | Batch RPC methods, client resilience, server concurrency | 3 |
| 6 | `phase-6-watcher-and-scheduling/` | Event filtering, SyncScheduler, scoped resync, self-write suppression | 3, 4, 5 (steps 1–2 can land earlier) |

Phase 1 is the highest-value fix (it stops data loss). Phase 2 is the foundation the
rest builds on. Phases 3–5 can proceed in that order; 4 can overlap 3. Phase 6's
event-filtering and scheduler (steps 1–2) are independently landable early; scoped
resync (step 3) needs phases 3–5.

## Reading order

Each phase folder contains:

- `00-phase-overview.md` — scope, dendrogram of the phase, exit criteria
- `01..0N-*.md` — step-by-step implementation docs (top-down: contract → data flow →
  code changes per file → edge cases)
- last file — verification: tests to add/run, invariants to assert

Start with `01-current-state-analysis.md` for the evidence (file:line) behind every
claim above.

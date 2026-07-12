# Phase 3 — Memory-Bounded Pipeline & Parse-Once

## Objective

Resync cost proportional to **what changed**, memory proportional to a **fixed window** —
not to project size. Concretely:

- No per-file RPC for unchanged files during change detection.
- No full-document DB snapshots.
- Each changed file is read once and parsed once per sync.
- Peak RAM ≈ window_size × avg_file_footprint, regardless of project size.

## Dendrogram (top → bottom)

```
resync(session)
│
├── SCAN (unchanged)                          scanner.py — hashes on disk
│
├── LEAN SNAPSHOT                             01-lean-db-snapshot.md
│   └── one triple query → rows {id, path, hash, physical_parent}
│       (feeds GroupResolver from Phase 1 — same query, shared)
│
├── ID RESOLUTION (cheap path first)          02-id-lookup-cache.md
│   ├── unchanged (path+hash match snapshot)   → id from snapshot, NO RPC
│   ├── changed/modified                       → id from snapshot by path, NO RPC
│   ├── unknown path, hash matches a DB row    → moved candidate; confirm id via
│   │                                            ONE batch RPC read (no injection)
│   └── truly new                              → batch RPC read_or_inject (writes IDs)
│
├── WINDOWED EXECUTION                        03-windowed-pipeline-parse-once.md
│   └── for each window W (default 100 changed files):
│       ├── read + parse once (resolve_mro=True) → keep AST in window scope
│       ├── Phase-1 collect: existing-map query batched for W parents
│       ├── Phase-2 analyze: reuse SAME AST + content (no re-parse, no re-read)
│       ├── stage all ops into SyncWriteBatch
│       └── drop content + AST before next window (bounded ledger)
│
└── FLUSH once (Phase 2 batch) + FINALIZE
```

## Why windows instead of the current two global phases

Today Phase 1 completes for ALL files (holding every file's content in
`collection_results`, phase_processor.py:220-240), then Phase 2 re-parses ALL files.
Two full passes, O(project) memory, duplicate parse. Windows interleave the phases per
chunk of files; call-resolution ordering is preserved because call edges reference
elements by stable ID and the final flush is a single transaction — within-sync ordering
across windows does not matter for correctness (verify with the cross-file-call e2e test,
doc 04).

## Docs

- `01-lean-db-snapshot.md` — replace `get_all` with triple-select snapshot + GroupResolver reuse.
- `02-id-lookup-cache.md` — hash-first ID resolution; injection only for new files; batch RPC.
- `03-windowed-pipeline-parse-once.md` — window runner, AST reuse, concurrency model, progress.
- `04-verification.md` — memory ceiling test, RPC-count test, equivalence test.

## Depends on

- Phase 2 (`SyncWriteBatch`) — windows stage, single flush.
- Phase 1 (`GroupResolver`) — shares the snapshot query.
- Enables Phase 5 batch RPC methods (client work lands there; this phase defines the need).

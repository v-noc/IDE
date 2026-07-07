# Phase 2 — Commit Batching & SyncWriteBatch (Unit of Work)

## Objective

One sync ⇒ **one logical TerminusDB commit**. Interactive edits ⇒ one commit per user
action (not per repo call). Repositories stop deciding when to commit; a write batch
owned by the caller does.

TerminusDB context: every commit is an immutable layer (git-style). Layers make history
queries and time-travel possible, but thousands of micro-commits ("Updating structure X",
"Moving item Y") slow reads, bloat storage, and make the versioning UI useless. The
fix is the same as git's: **stage everything, commit once, with a meaningful message.**

## Dendrogram (top → bottom)

```
SyncWriteBatch (new: app/core/repository/write_batch.py)
│
├── stage_*  (pure accumulation, no I/O)
│   ├── stage_insert(node | schema)          → insert_document op
│   ├── stage_update_fields(id, {field:val}) → update_triple ops   (no read-modify-write)
│   ├── stage_delete(id, parent_fields)      → delete_document + parent-edge cleanup
│   ├── stage_move(id, new_parent, field)    → delete old edge + add new edge
│   └── stage_content(file_id, text)         → CodeContent upsert
│
├── flush(commit_msg, *, chunk_bytes, chunk_ops)
│   ├── merge ops → ONE WOQL and-query        (order: deletes → inserts → edges → updates)
│   ├── payload-bound chunking ONLY if needed → "sync 3f2a part 2/3"
│   └── clear buffers; return FlushReport {ops, chunks, commit_ids}
│
└── consumers
    ├── orchestrator: one batch per resync    (collector + phases stage into it)
    ├── services: one batch per API action    (group create+move already atomic — model)
    └── migration/bootstrap
```

## Commit budget (exit criteria)

| Operation | Commits today | Commits after |
|---|---|---|
| resync, no changes | 0 | 0 |
| resync, N files changed | 5–20+ (grows with N) | 1 (payload chunks only when >budget) |
| save one file (watcher) | 3–6 | 1 |
| create group + move 10 items | 1 (already good) | 1 |
| single node update via API | 1 (+1 read) | 1 (no pre-read) |

## Docs in this phase

- `01-sync-write-batch.md` — the WriteBatch itself: op model, ordering, chunking,
  dedup/merge rules.
- `02-repo-commit-discipline.md` — refactor repos to stage into a batch; remove
  read-modify-write updates; kill per-call commits.
- `03-terminusdb-practices.md` — commit messages, layer maintenance (`optimize`/squash),
  payload limits, `last_data_version` optimistic concurrency, snapshot query hygiene.
- `04-verification.md` — commit-count assertions, atomicity tests.

## Depends on / enables

- Independent of Phase 1 (touches write path, not detection) — can run in parallel.
- Enables Phase 3 (windowed pipeline stages into the same batch) and Phase 4 (repo split
  becomes trivial once repos are commit-free primitives).

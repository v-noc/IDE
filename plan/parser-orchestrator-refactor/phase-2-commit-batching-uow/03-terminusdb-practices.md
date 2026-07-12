# Phase 2 / Step 3 — TerminusDB operating practices

Codify how this codebase talks to TerminusDB. These rules back the WriteBatch design and
carry into Phases 3–4.

## 1. Commits are layers — budget them

- A commit = an immutable layer delta. Reads traverse layers; long uncompacted chains
  slow every query.
- **Budget**: interactive action ⇒ 1; resync ⇒ 1 (+payload chunks); background jobs ⇒ 1
  per job. Enforced by WriteBatch being the only commit path.
- **Message format**: `[{session_id}] {verb} {summary}` e.g.
  `[3f2a1c] sync: 12 files, 4 folders, 87 elements, 210 calls`. The versioning UI
  (api/v1/versioning/commits.py) becomes readable for free.

## 2. Layer maintenance (new, currently missing entirely)

Add `app/core/services/db_maintenance.py`:

```
after each successful resync flush:
    commit_count_since_optimize += chunks
    if commit_count_since_optimize ≥ N (default 200):
        POST optimize on the project db (admin mixin — add optimize() to
        db/terminus_client/database.py if absent; endpoint: /api/optimize/<path>)
```

- Optimize/squash compacts layers without losing commit history semantics needed by the
  app (verify: the versioning UI reads commit log via `_commits` graph — optimize keeps
  it; **test this against a real instance before enabling by default**).
- Run in a background task after `progress_tracker.complete()` — never block sync.
- Config: `settings.py` knobs `db_optimize_every_n_commits`, `db_optimize_enabled`.

## 3. Query hygiene for snapshots

- **Never `get_all_documents` for detection-style reads.** Select triples:
  ids + the 2–3 fields you compare (path, hash). Full docs pull children sets,
  descriptions, theme configs — 10–50× the bytes, all discarded.
  (Applied in Phase 1 step 02 via `get_snapshot_rows`; generalized in Phase 3.)
- Path queries (`get_children_by_path`) with unbounded `+` on big files are the current
  per-file cost — Phase 3 batches them per window with `member()` over parent ids.
- Prefer `read_document` only for nodes that will be *returned to the user*.

## 4. Optimistic concurrency

- The client already threads `last_data_version` (document.py mixin). WriteBatch flush
  should capture the data version from its first read (if the owning flow performed one)
  and pass it on the commit; on `DataVersionMismatch` → retry once by re-staging against
  fresh reads, then surface a conflict error.
- Matters for: watcher resync racing an interactive edit (two writers, same branch).
  Today the race silently interleaves commits; after: second writer retries cleanly.

## 5. Payload limits

- 4 MiB default chunk budget (measured safe for local TerminusDB; make it
  `settings.db_max_payload_bytes`).
- Big file contents dominate: `stage_content` ops chunk independently — a 10 MB source
  file becomes its own part-commit rather than failing the whole flush
  (restores the intent of the commented-out `_chunk_file_content_pairs`,
  phase_processor.py:26-51,135-141).

## 6. Branch/ref scoping

- Keep `ProjectUoW`/`scoped_client` as the only place db/branch/ref are set. WriteBatch
  refuses to flush on a client with `ref` set (read-only historical view) — assert early
  with a clear error instead of a TerminusDB 400.

## 7. Schema notes (observed, act in Phase 4)

- `CodeContentSchema` split from `FileSchema` is correct (small doc + heavy blob apart) —
  keep.
- `code_position` as subdocument forces the delete/insert/relink dance
  (code_element_repo.py:209-236). Consider flattening position into 4 scalar fields on
  the element — removes a subdocument per element and simplifies updates to 4
  update_triples. Migration cost is real: decide in Phase 4, not here.

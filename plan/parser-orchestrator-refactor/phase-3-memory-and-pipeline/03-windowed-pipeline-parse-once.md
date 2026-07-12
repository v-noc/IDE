# Phase 3 / Step 3 — Windowed pipeline, parse once

Files: `orchestrator.py`, `utils/phase_processor.py`, `collection/collector.py`,
`analysis/body_parser.py`

## Window runner (top)

Replace the two global phases with a per-window loop. The orchestrator shrinks to:

```python
async def resync(self):
    session = SyncSession(...)              # batch, progress, caches, session_id
    scan     = self.scanner.scan()
    snapshot = await DbSnapshot.load(self.repos)
    changes  = await self.detector.detect(scan, snapshot)
    if not changes.has_changes(): return changes

    await self.structure_planner.stage(changes, scan, session.batch)   # folders/files/content shells

    for window in chunked(changes.files_needing_parse(), WINDOW_SIZE):  # default 100
        await self.window_runner.run(window, session)                   # collect+analyze+stage
        session.release_window()                                        # drop content/AST

    await session.batch.flush(f"sync: {changes.summary()}")
    await session.finalize()                # progress complete, socket, maintenance hook
```

`files_needing_parse` = new + modified + moved (same set as today,
orchestrator.py:195-202).

## Inside a window (middle)

```
window_runner.run([f1..f100], session)
│
├── 1. read + parse ONCE per file (bounded gather, semaphore = max_concurrent_files)
│      parse_result = driver.parse_file(path, content, resolve_mro=True)
│      ├── id verification hook (step 02)
│      └── ParsedFile {file_node, ast_nodes, content}  — lives only in this window
│
├── 2. existing-map for the WHOLE window in one query
│      current: ast_processor._build_existing_map → 1 path-query PER FILE
│      new:     repos.structure_repo.get_children_bulk(parent_ids=[...])
│               (WOQL: member(v:start, ids) + same path pattern — one round-trip)
│
├── 3. collect: ast_processor.sync_content per file (pure diff vs existing map)
│      → stage element inserts/updates/deletes/moves + content into session.batch
│
├── 4. analyze: body_parser.process_ast REUSES ParsedFile.ast_nodes + content
│      ├── delete the re-parse (body_parser.py:194-204) and re-read (187-192)
│      ├── delete the second get_children (body_parser.py:173) — reuse window map
│      └── resolve_calls per scope (driver RPC) → stage call ops into session.batch
│
└── 5. release: del ParsedFile list; if session.batch.estimated_bytes() > budget,
       partial flush (payload chunking from Phase 2 makes this safe + labeled)
```

### MRO note

Phase 1 parses with `resolve_mro=True`, Phase 2 with `False` — the only delta is MRO
enrichment on class nodes, so the single `resolve_mro=True` parse strictly supersedes
the second parse. Verify with the parser unit tests (`tests/unit/parser/`).

### Concurrency model (replace the three overlapping knobs)

| Knob today | Problem | After |
|---|---|---|
| orchestrator `max_concurrent_files=50` + PhaseProcessor semaphore | duplicated | one `parse_concurrency` on WindowRunner |
| `max_concurrent_db=100` semaphore | unused for batching now | dropped — DB writes go through the batch |
| `_ANALYSIS_PHASE_CONCURRENCY=10` chunks + inner `Semaphore(1)` (body_parser.py:298) | inner semaphore serializes scopes anyway | one `resolve_concurrency` for resolve_calls RPCs (default 8), scopes of one file processed sequentially (they share driver project state) |
| `batch_size` 5000 vs 4000 mismatch | two defaults | single `window_size` + byte budget |

All knobs live in one `PipelineConfig` dataclass on settings.

## Progress reporting

`ProgressTracker` phases become `scanning → detecting → syncing (window i/k, file x/y)
→ finalizing`. It already supports totals + current-file
(progress.py); update phase names, keep the socket contract
(`sync_started/sync_complete/project:updated` unchanged for the frontend).

## Steps (bottom)

1. Introduce `SyncSession` (holds batch, progress, id-cache handle, metrics) and
   `PipelineConfig`.
2. Add `get_children_bulk` (one `member` + path query; returns rows tagged by start id).
3. Build `WindowRunner.run` = move `collector.process_file` (minus its own file-read
   and driver dance) + `body_parser.process_ast` (minus re-read/re-parse/re-query) into
   the window flow described above. Keep `ASTProcessor` and `CallChainBuilder`
   internals — they are the diff brains and don't change.
4. Rewrite `orchestrator.resync` to the ~20-line loop above; delete `PhaseProcessor`
   (its stats/timeout wrappers move into WindowRunner; keep `tracker.timer` spans).
5. Delete `_chunk_file_content_pairs` (Phase 2 batch owns byte-chunking).
6. Replace all `print()` in the pipeline with logger calls (carry `session_id`).

## Failure isolation

Per-file failure (read/parse/diff) logs with session id, increments
`files_failed`, and skips the file — same policy as today
(phase_processor.py:201-211) but recorded in `FlushReport.metrics` and surfaced in the
`sync_complete` socket payload so the UI can say "synced with 2 errors" instead of
pretending success.

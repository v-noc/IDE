# Phase 3 / Step 4 — Verification

## Equivalence (the gate for everything else)

Golden test: parse `examples/sample_project` (and the richer
`tests/unit/parser/analyzer/simple_project/`) with the **old** pipeline, dump the graph
(all documents ordered by id, normalized timestamps) — commit as fixture. New pipeline
must produce an identical dump. Run per PR in this phase.

Cross-file/cross-window ordering case: project where `a.py` (window 1) calls into
`z.py` (window 2) and vice versa → all call edges present after single flush.

## RPC-count budget

Fixture: 200-file project, 5 files modified.

| Metric (per resync) | Before | Budget after |
|---|---|---|
| `read_or_inject_file_id` calls | 200 | 0 (5 lazy-verified via parse) |
| `parse_file` calls | 10 (5×2) | 5 |
| file reads from disk | 10+ | 5 |
| WOQL path queries (existing maps) | 10 (5×2 phases) | ⌈5/window⌉ = 1 |
| snapshot queries | 2 full-doc get_all | 1–2 triple selects |

Implement counters as a test fixture wrapping `JsonRpcLanguageDriver._call` and
`AsyncClient.query` — also useful in production metrics later.

## Memory ceiling

Test: generate 2,000 synthetic files (~4 KB each) → resync with `window_size=100` →
sample `tracemalloc` peak between windows. Assert peak stays under
`window_size × avg_file × safety(4)` and does **not** scale when file count doubles.
(Slow test — mark `@pytest.mark.perf`, run nightly not per-PR.)

## Behavior checks

1. **Id verification reclassify**: replace a file's contents entirely (different
   embedded id) → resync → old element subtree deleted, new one created, no orphan
   CodeContent (extends `tests/unit/parser/analyzer/hierarchy/test_file_ops.py`).
2. **Window partial flush**: set byte budget tiny → sync a 3-file project → flush
   parts committed with `part i/k`, graph complete.
3. **Failure isolation**: file with a driver-crash (fixture syntax bomb) among 10 →
   9 synced, 1 reported in `sync_complete` payload, session flush still 1 commit.

## Perf numbers to record here after landing

- resync unchanged 2k files: before ___ s → after ___ s (target: <1 s, snapshot+scan only)
- resync 5 modified of 2k: before ___ s → after ___ s
- peak RSS during full first sync: before ___ MB → after ___ MB

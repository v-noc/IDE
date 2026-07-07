# Phase 2 / Step 4 — Verification

## WriteBatch unit tests (pure, no DB)

`tests/unit/repository/test_write_batch.py`

1. **Dedup table** — every row of the merge table in doc 01 (insert→update collapses,
   insert→delete cancels, edge last-wins, …).
2. **Ordering** — staged out of order, flushed WOQL has deletes → inserts → edges →
   updates (inspect generated query dict, no server needed).
3. **Chunking** — ops with `est_bytes` crossing the budget split into parts;
   messages carry `part i/k`; a single op larger than budget goes alone.
4. **Empty flush** — zero ops ⇒ zero client calls.
5. **Failure semantics** — client raises on chunk 2 of 3 ⇒ `WriteBatchError` with
   report showing chunk 1 committed, 2 failed, 3 not attempted.
6. **code_position swap translator** — regression for the delete/insert/relink pattern.
7. **base_classes replacement** — removed base class actually deletes its triple.

## Commit-count integration tests (real TerminusDB, extend e2e harness)

`tests/e2e/core/test_commit_budget.py` — helper:

```python
async def commit_count(client) -> int:  # via versioning commits endpoint
```

| Scenario | Assert |
|---|---|
| fresh project sync | commits == 1 (+ known bootstrap commits) |
| resync unchanged | +0 |
| touch 1 file → resync | +1 |
| modify 50 files → resync | +1 (or +k with k == payload chunks, k reported) |
| API: create group with 10 children | +1 |
| API: update node name | +1, and **no read** issued beforehand (assert via client call-log fixture) |

## Atomicity tests

1. Kill the flush mid-way (inject failure into chunk 2): DB state contains chunk 1 only;
   re-running resync converges (idempotence) — documents the crash-consistency story.
2. Concurrent writer (`last_data_version` mismatch): batch retries once, succeeds;
   assert exactly 2 attempts.

## Regression sweep

- Full existing suites: `tests/unit/service/`, `tests/e2e/core/` — all repo behavior
  reachable through services must be unchanged in results (only commit granularity
  changed).
- Grep gates in CI:
  - `commit_msg=` outside `write_batch.py`/migration ⇒ fail
  - `print(` under `app/core/repository` ⇒ fail (prep for Phase 4)

## Perf sanity

Measure resync wall-time on `examples/sample_project` before/after: expect neutral or
better (fewer HTTP round-trips, no read-before-update). Record numbers in this file.

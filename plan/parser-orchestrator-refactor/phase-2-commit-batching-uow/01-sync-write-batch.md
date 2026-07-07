# Phase 2 / Step 1 — SyncWriteBatch

New file: `app/core/repository/write_batch.py`

## Op model (top)

```python
@dataclass
class WriteOp:
    kind: Literal["insert_doc", "delete_doc", "update_triples",
                  "add_edge", "delete_edge", "upsert_doc"]
    target_id: str
    payload: Any                    # schema dict | {field: value} | (parent, field)
    est_bytes: int                  # for payload chunking
    dedup_key: tuple                # see merge rules

class SyncWriteBatch:
    def __init__(self, client: AsyncClient, *, session_id: str): ...
    # stage_* methods append WriteOps — synchronous, no I/O, safe from any coroutine
    async def flush(self, message: str, *, squash_hint: bool = False) -> FlushReport: ...
    def pending_ops(self) -> int: ...
    def estimated_bytes(self) -> int: ...
```

`session_id` = short uuid per resync/API action; every commit message and log line
carries it (correlates commits ↔ logs ↔ progress events).

## Merge & dedup rules (middle)

Staging the same target twice must collapse — this is what "avoid unnecessary commits"
means *inside* a batch too:

| Sequence on same id | Collapses to |
|---|---|
| insert → update_triples | insert (with merged fields) |
| insert → delete | nothing |
| update → update (same field) | last wins |
| add_edge(p1) → add_edge(p2) same field | last wins (single-parent fields) |
| delete_edge → add_edge same (parent, field, child) | nothing |
| upsert_content → upsert_content | last wins |

Keyed by `dedup_key`: `(kind_class, target_id, field?)`. Implemented as an ordered dict —
preserves first-staged order for unrelated ops (WOQL `and` executes as one transaction,
but deterministic order keeps diffs reviewable and reproduces bugs).

## Flush algorithm

```
flush(message):
1. if no ops → return empty report (NO empty commits — this is the "resync with no
   changes creates nothing" guarantee)
2. order ops: delete_doc → insert_doc → edges (delete then add) → update_triples → upserts
   (inserts before edges because add_triple to a not-yet-inserted doc fails;
    matches current flush_batch logic structure_repo.py:235-251)
3. partition into chunks where sum(est_bytes) ≤ MAX_PAYLOAD (default 4 MiB — revive the
   constant from phase_processor.py:20 that is currently commented out) and
   len(chunk) ≤ MAX_OPS (default 2000, from max_queries_per_code_flush)
4. single chunk  → client.query(and(ops), commit_msg=f"[{session_id}] {message}")
   k chunks      → commit_msg=f"[{session_id}] {message} (part i/k)"
5. on chunk failure: raise WriteBatchError carrying FlushReport of committed chunks —
   caller decides (orchestrator: abort sync, mark progress error, leave batch content
   for retry; do NOT silently continue like phase_processor.py:152 does today)
```

Document/content ops that cannot be expressed as WOQL (full doc insert with subdocs) use
`Doc(schema)` inside the same `and` — exactly what `structure_repo.flush_batch` and
`code_element_repo.flush_batch` already prove works. Those two methods are the seed
code: **lift, generalize, delete the originals** (step 02).

## Content-size ledger

`stage_content` records `est_bytes = len(text.encode("utf-8"))`. The batch exposes
`estimated_bytes()` so Phase 3's windowed pipeline can flush early when the ledger
crosses the payload budget — replacing today's count-only `batch_size >= 5000` flush
trigger (phase_processor.py:233) that ignores byte size.

## Steps (bottom)

1. Create `WriteOp`, `SyncWriteBatch`, `FlushReport`, `WriteBatchError`.
2. Port the WOQL emission from `structure_repo.flush_batch` (insert/delete/move) and
   `code_element_repo.flush_batch` (triple-level updates, code_position subdocument
   replace, content upserts) into op → WOQL translators. Keep the tricky
   code_position swap (code_element_repo.py:209-236) as its own translator with a test.
3. Implement dedup/merge table above with unit tests (pure, no DB).
4. Implement chunked flush + failure semantics.
5. Wire ONE consumer end-to-end as proof: `collector.sync_structure` stages into a batch
   the orchestrator owns, orchestrator flushes once after Phase 2 analysis. Commit count
   for a small resync drops to 1 — measure via versioning API.

## Non-goals

- Cross-request transactionality (batch lives within one request/sync).
- Rewriting every service call site — that is step 02.

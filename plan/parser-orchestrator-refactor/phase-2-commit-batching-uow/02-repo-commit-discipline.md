# Phase 2 / Step 2 — Repository commit discipline

Rule after this step:

> **Repositories never pass `commit_msg` to the client.** They either (a) answer read
> queries, or (b) stage ops into a `SyncWriteBatch` handed to them. The batch owner
> (orchestrator, service action, migration) flushes.

## Migration map (top)

All 49 commit sites, grouped:

| Site group | Today | After |
|---|---|---|
| `BaseRepo.create_nodes` (base_repo.py:32) | insert_document + commit per call | `stage_insert`; service flushes |
| `BaseRepo.update_node/update_nodes` (113/135) | get_by_ids → merge → update_document (2 round-trips, full-doc rewrite) | `stage_update_fields` with only changed fields — **no pre-read** |
| `BaseRepo.delete_*_with_parent_cleanup` (163/183) | query + commit | `stage_delete` (edge cleanup ops included) |
| `BaseRepo.move_item_by_type / move_batch_by_type` (294/332) | query + commit each | `stage_move` |
| `structure_repo.flush_batch / update_batch / flush_content_batch` | own WOQL + commit | deleted — translators moved into WriteBatch (step 01) |
| `code_element_repo.flush_batch / update_batch` | own WOQL + commits per chunk | deleted — same |
| `call_repo.create / flush_delete_move_batch_chunked / batch_delete_calls` | commits per chunk | stage into batch; chunking handled by flush |
| group repos `create_and_move_items` (structure_group.py:91) | one query+commit (already atomic ✅) | same behavior via batch — keep atomicity, gain uniform code |
| services (project/document/log/test/playground) | repo-per-call commits | one batch per API handler |

## Killing read-modify-write updates (middle)

Today every update pre-reads the doc to preserve set-fields
(`merge_set_fields`, base_repo.py:105) because `update_document` replaces the whole doc.
With triple-level updates this disappears:

```python
# update only what changed — children edges are never touched by a field update
batch.stage_update_fields(node.id, {
    "qname": node.qname,
    "path": node.path,
    "updated_at": now,
})
```

- The WOQL pattern already exists in `code_element_repo.flush_batch`
  (opt-delete-old-triple + add-new-triple, lines 239-262) — reuse the translator.
- **Delete the merge-preserve machinery**: `merge_fields`, `merge_set_fields`,
  `STRUCTURE_SET_FIELDS_TO_PRESERVE`, `CODE_SET_FIELDS_TO_PRESERVE` consumers in update
  paths. (The constants stay — GroupResolver and readers still use the field lists.)
- `base_classes` set replacement (code_element_repo.py:265-270) currently only **adds**
  triples — it never deletes removed base classes: fix in the translator
  (delete all `base_classes` triples, re-add) and add a regression test.

## Interactive service actions (one action = one commit)

Handlers in `api/v1/*` construct a batch via dependency:

```python
async def move_items(payload, uow: ProjectUoW = Depends(...)):
    batch = uow.new_write_batch()            # ProjectUoW owns client + session id
    service.move_batch(batch, payload.moves) # stages
    await batch.flush(f"Move {len(payload.moves)} items")
```

`ProjectUoW` (db/context.py) gains `new_write_batch()` — natural home since it already
scopes client/branch/ref. Guard: `readonly` UoWs (`ref`/`compare_to` set) refuse to
create batches.

## Bug fixes to fold in (they live on this path)

1. **Module-constant mutation**: `structure_repo.move_item/move_batch` (lines 108-119)
   mutate `STRUCTURE_CHILD_TYPE_TO_FIELD` globally. Build the merged dict locally:
   `{**STRUCTURE_CHILD_TYPE_TO_FIELD, **CODE_CHILD_TYPE_TO_FIELD}`.
2. **`move_item_by_type` duplicate add** (base_repo.py:314-319): nested
   `add_triple(...).opt(add_triple(...))` adds the edge twice (set semantics saves us,
   but the query is wrong). The staged translator replaces it.
3. Swallowed failures returning `None/False` — batch flush raises typed errors instead
   (full error-model work in Phase 4; here just don't add new `print`s).

## Steps (bottom)

1. Add `ProjectUoW.new_write_batch()`; thread a batch through
   `GraphBuilderOrchestrator` → `Collector` → `PhaseProcessor` → `BodyParser`
   (constructor param, replacing their direct `repos.*.flush_*` calls).
2. Convert repos in this order (each its own PR, tests green between):
   a. structure_repo (+ collector) — resync path
   b. code_element_repo (+ ast_processor/phase_processor)
   c. call_repo (+ body_parser buffers: keep the in-memory buffers/thresholds,
      point their flush at `batch.stage_*`; thresholds now trigger *payload* pre-checks,
      not commits — see phase 3 for windowing)
   d. group repos + group_service
   e. remaining services (document, log, test, playground, project)
3. Delete dead repo methods; grep `commit_msg=` under `app/core/repository` and
   `app/core/services` must return only `write_batch.py`.
4. Keep `migration/migrate_db.py` and bootstrap on explicit batches with their own
   messages.

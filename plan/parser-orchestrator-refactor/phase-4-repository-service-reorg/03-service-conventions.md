# Phase 4 / Step 3 — Service layer conventions

## Shape of a service method

```python
class StructureService:
    def __init__(self, uow: ProjectUoW):
        self.uow = uow
        self.reads = uow.repos.structure          # read façade
    async def move_items(self, moves: list[MoveSpec]) -> MoveResult:
        batch = self.uow.new_write_batch()
        for m in moves:
            self._stage_move(batch, m)            # validation + staging
        await batch.flush(f"Move {len(moves)} items")
        return MoveResult(...)
```

Conventions:

1. **One public method = one use case = one commit.** No service calls another
   service's write path; shared logic is a staging helper.
2. Services accept/return **domain types** (nodes, dataclasses) — never raw dicts,
   never WOQL, never `raw=True` escapes (grep shows `raw=True` leaking into services
   today via `group_service.update_basic_info`, group_service.py:96).
3. Read-only ctx (`uow.readonly`) guards writes at service entry with `ConflictError`,
   not deep inside repos.

## GroupService cleanup (worked example)

`services/group_service.py` dispatches type→repo/node/schema through three
if/elif ladders (lines 22-50). Replace with the `mapping.py` registry:

```python
GROUP_FAMILY = {
    GroupType.STRUCTURE:    Family(repo="structure_group", node=StructureGroupNode, schema=StructureGroupSchema),
    GroupType.CODE_ELEMENT: Family(...),
    GroupType.CALL:         Family(...),
}
```

Also fold in Phase 1 semantics: group deletion re-parents children to the group's
**logical** parent (structure_group.py:47-89 already does this physically via WOQL —
keep, but route through the batch and reuse for all three families instead of only
structure).

## Duplication to collapse

| Duplicated today | Single home after |
|---|---|
| folder/file `prepare_batch` + `_add_*` trios (folder_processor.py, file_processor.py) | one `StructurePlanner` parameterized by kind (they differ only in node ctor + content handling) |
| `update_batch` in structure/code repos | gone (Phase 2) |
| move-batch WOQL in 3 repos | `batch.stage_move` |
| type ladders in group_service + repos `_to_node` + child_raw parsers | `mapping.py` registry |
| `qname_for_rel_path` (folder_processor.py:125) vs file_processor equivalent | `utils/qname.py` |

## Schema decision to make this phase

**Flatten `code_position` subdocument** (see phase-2/03 §7): 4 scalar fields on
Function/Class/Call schemas.

- Pro: kills the delete/insert/relink translator, −1 document per element,
  simpler updates and reads.
- Con: schema migration on existing project DBs (`migration/migrate_db.py` needs a
  real migration: add fields, copy values, drop subdocument links).
- Decision gate: if migration tooling is not ready, defer — the translator from
  Phase 2 keeps working; do not block the phase on this.

## API routes touch-up

- Routes in `api/v1/*` keep their contracts (frontend untouched), but move inline
  orchestration into services (`project_routes.py:121-125` builds the orchestrator
  in-route today; move behind `ProjectService.resync(project_id)` so the watcher and
  the route share one entry — prerequisite for Phase 6's single scheduler).
- Dependencies: `api/dependencies.py` provides `ProjectUoW`; add `get_service(...)`
  helpers so routes stop constructing services ad hoc.

## Steps

1. `ProjectService.resync` unification (route + watcher call the same method).
2. GroupService registry rewrite + logical-parent delete semantics.
3. StructurePlanner merge of folder/file processors.
4. Service-by-service sweep to the convention shape (structure, code_element, call,
   document, log, test, playground, container) — mechanical after 1–3.
5. Decide + (maybe) execute code_position flattening behind a migration.

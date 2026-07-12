# Phase 4 / Step 1 — BaseRepo decomposition

Method-by-method destination map for `app/core/repository/base_repo.py` (439 lines):

| BaseRepo member | Lines | Destination |
|---|---|---|
| `create_nodes` | 32-62 | delete — `batch.stage_insert` (Phase 2) |
| `get_by_id / get_by_ids / get_all` | 64-97 | `repos/<aggregate>.py` façade (typed, raising) |
| `merge_fields / merge_set_fields / touch_updated_at` | 99-111 | delete (read-modify-write gone in Phase 2) |
| `update_node / update_nodes` | 113-161 | delete — `batch.stage_update_fields` |
| `delete_with_parent_cleanup` (+batch) | 163-203 | delete — `batch.stage_delete` |
| `get_children_by_path` | 205-292 | `queries/children.py` — pure builder + executor |
| `move_item_by_type / move_batch_by_type` | 294-378 | delete — `batch.stage_move` (fixes the double-add bug at 314-319) |
| `find / get_by_qnames` | 380-438 | `queries/lookup.py` |
| `_to_schema / _to_node / _ensure_list` | 20-30 | `mapping.py` |

## Per-aggregate repos after the split

Example — `repos/structure.py`:

```python
class StructureReads:
    def __init__(self, executor: QueryExecutor): ...
    async def by_id(self, id) -> StructureNode            # raises NotFoundError
    async def by_ids(self, ids) -> list[StructureNode]
    async def children(self, parent_id, *, types, depth) -> list[StructureNode]
    async def snapshot(self) -> DbSnapshot                # Phase 3
    async def parent_file(self, item_id) -> FileNode | None

class StructureStaging:      # thin sugar over SyncWriteBatch, keeps field names local
    def insert_folder(self, batch, node): batch.stage_insert(FolderSchema.from_pydantic(node))
    def move(self, batch, id, parent, child_type): batch.stage_move(id, parent, FIELD[child_type])
    ...
```

- The union-type dispatch (`structure_repo._to_node/_to_schema`, lines 67-85) moves to
  `mapping.py` as one registry: `{"FolderSchema": FolderNode, ...}` — the same table
  `child_raw.py` parse functions already encode; merge them (single source for
  type ⇄ node ⇄ schema ⇄ child-field).
- `structure_repo.get_by_qnames` returning a dict while the base returns a list
  (structure_repo.py:193-195) — fix signature: `qname_index(...) -> dict[str, Node]` as
  a distinct method name.
- `Repositories` container (`repository/__init__.py`) keeps its shape so `ProjectUoW`
  and call sites migrate incrementally — its attributes become the new façades.

## Query builders (`queries/`)

- `children.py`: keep the WOQL from `get_children_by_path` including the
  `include_call_target_docs` branch (base_repo.py:246-263) and the depth/`{n,m}`
  handling; parameterize path fields from the merged registry. Add
  `children_bulk(parent_ids)` (Phase 3 step 03 needs it).
- `lineage.py`: `get_node_lineage` (code_element_repo.py:357) — already group-aware,
  just relocate.
- Executor owns the `client.query` call, error wrapping (`DbError`), and binding
  parsing (today duplicated in 6 methods: bindings-loop + `parse_*` + None-filter).

## Order of operations (bottom)

1. Create `mapping.py` (merge `child_raw.py` parse functions + `_to_node` dispatchers +
   field registries). Everything imports from here; `child_raw.py` re-exports during
   transition.
2. Create `queries/` with executor + children/lookup/lineage; port callers
   (services, ast_processor, tree_builder) one by one.
3. Shrink each concrete repo to façade + staging sugar; delete from `BaseRepo` as the
   last caller leaves. `BaseRepo` file deleted at the end (grep gate).
4. `call_repo`, `log_repo`, `document_repo`, `container_repo`, `project_repo`,
   `play_ground_repo`, `test_repo` follow the same map — do structure/code_element
   first (they anchor the pipeline), the rest mechanically.

Each move is behavior-preserving; the golden-graph test from Phase 3 plus
`tests/unit/service/*` are the safety net.

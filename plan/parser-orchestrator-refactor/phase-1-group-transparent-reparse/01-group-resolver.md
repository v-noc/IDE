# Phase 1 / Step 1 — GroupResolver

New module: `app/core/parser/graph_builder/discovery/group_resolver.py`

The single source of truth for "jumping" groups. Everything else in the pipeline asks
this object instead of re-implementing group logic (today it is re-implemented — and
diverges — in `change_detector.py`, `ast_processor.py`, `diff_calulator.py`).

## Contract (top)

```python
@dataclass(frozen=True)
class ParentInfo:
    physical_parent_id: Optional[str]   # direct edge holder (may be a group)
    logical_parent_id: Optional[str]    # first non-group ancestor
    owning_group_id: Optional[str]      # innermost group between item and logical parent
                                        # None if item is not grouped

class GroupResolver:
    @classmethod
    async def load(cls, repos: Repositories, *, families: GroupFamilies) -> "GroupResolver": ...
    def parent_info(self, item_id: str) -> ParentInfo: ...
    def logical_children(self, container_id: str) -> set[str]: ...   # groups flattened
    def is_group(self, node_id: str) -> bool: ...
```

`GroupFamilies` selects which edge sets to load:

| Family | Group schema | Group child edges | Container edges pointing at groups |
|---|---|---|---|
| structure | `StructureGroupSchema` | `folder_children`, `file_children`, `structure_group` | `structure_group` |
| code | `CodeElementGroupSchema` | `function_children`, `class_children`, `code_element_group` | `code_element_group` |
| call | `CallGroupSchema` | `call_children`, `call_group` | `call_group` |

Edge names come from the existing registry `repository/utils/child_raw.py` — do **not**
duplicate the literals; import `STRUCTURE_FIELDS`, `CODE_ELEMENT_FIELDS`, `CALL_FIELDS`.

## Data flow (middle)

```
GroupResolver.load()
│
├── 1 WOQL query per family (NOT per node):
│      select v:parent, v:field, v:child, v:parent_type
│      where  v:parent v:field v:child
│        and  v:field in <family edge list>
│        and  v:parent rdf:type v:parent_type
│   → edge list [(parent_id, field, child_id, parent_type)]
│
├── build maps in memory:
│      physical_parent[child_id] = parent_id
│      group_ids = {id where parent_type or child @type is a *GroupSchema}
│
└── logical resolution (lazy, memoized):
       logical(id):
           p = physical_parent.get(id)
           while p is not None and p in group_ids:
               innermost_group ??= p
               p = physical_parent.get(p)
           return p
```

Implementation notes:

- **One query, no documents.** Only triples — no `read_document`. This is also the seed
  of Phase 3's lean snapshot; design the query helper so `db_snapshot.py` can reuse it.
- **Cycle guard**: cap ancestor walk at e.g. 64 hops; on cycle, log a structured warning
  with the id chain and return `logical_parent_id=None` (treat as root, never emit a move
  for it — fail safe means "don't touch").
- **Empty/missing group edges**: an item with no physical parent (e.g. root folders,
  `INIT_FOLDER_ID` children) resolves to `logical_parent_id=None`. The change detector
  already treats the virtual root specially (`change_detector.py:371`), keep that.
- Memoize `logical()` results in a dict — the walk amortizes to O(nodes).

## Steps (bottom — do in this order)

1. Add `GroupFamilies` enum + edge-set lookup built from `child_raw.py` constants.
2. Implement the triple query in a new repo method
   `structure_repo.get_edge_triples(fields: tuple[str, ...]) -> list[Edge]`
   (see phase-4 for where this method ultimately lives; for now put it on `BaseRepo`).
3. Implement `GroupResolver.load / parent_info / logical_children / is_group` with
   memoization and cycle guard.
4. Extract `diff_calulator._flatten_calls_skipping_groups` + `_is_group_node`
   (call_graph/diff_calulator.py:127-151) into `group_resolver.flatten_skipping_groups()`
   and make `DiffCalculator` call it — one behavior, one place.
5. Unit tests (no DB): feed synthetic edge lists — nested groups (group in group),
   group at root, cycle, missing parent — assert `ParentInfo` for each.

## Out of scope for this step

- No change-detector integration yet (doc 02).
- No write-path changes (doc 03).

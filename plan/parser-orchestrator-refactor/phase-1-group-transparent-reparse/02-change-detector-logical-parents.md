# Phase 1 / Step 2 — ChangeDetector compares logical parents

File: `app/core/parser/graph_builder/discovery/change_detector.py`

## Decision table (top)

For each common ID (exists in DB and on disk):

| DB logical parent vs FS parent | hash | Result |
|---|---|---|
| same | same | unchanged (also when only the *physical* parent differs — i.e. grouped) |
| same | different | `modified` — content changed in place; **group edge untouched** |
| same, path/qname changed (rename in same dir) | any | `modified` — update doc fields only, **no move op** |
| different | any | `moved` — genuine FS move; MoveEvent carries group context |

Today the comparison at `change_detector.py:256` and `:328` uses raw
`db_parent != current_parent`, where `db_parent` is *physical*. That is the bug.

## Changes (middle)

### 1. Build the DB-side maps from GroupResolver

Replace `_build_parent_maps` (line 103) usage in `detect_changes`:

```python
resolver = await GroupResolver.load(self.repos, families=GroupFamilies.STRUCTURE)
# for each db id:
info = resolver.parent_info(item_id)
db_logical_parent  = info.logical_parent_id
db_owning_group    = info.owning_group_id
```

Keep `_build_parent_maps` only as a fallback for unit tests, or delete it once tests are
migrated. Note the resolver's triple query replaces the need for
`folder.children_by_type` parsing entirely.

### 2. FS-side maps unchanged

`_build_current_parent_maps` (line 183) already produces the *logical* truth — the
filesystem has no groups. No change.

### 3. Classification uses logical parents

In `_classify_folder_changes` (line 213) and `_classify_file_changes` (line 283):

```python
db_parent = resolver.parent_info(item_id).logical_parent_id   # was: physical map
current_parent = current_*_parent_by_id.get(item_id)

if db_parent != current_parent:
    moved.append(MoveEvent(
        id=item_id,
        old=db_node_path,
        new_path=current_path,
        new_parent_id=current_parent,
        old_group_id=resolver.parent_info(item_id).owning_group_id,  # NEW field
    ))
```

Add `old_group_id: Optional[str] = None` to `MoveEvent` (line 28). Downstream
(doc 03) uses it for the move policy.

### 4. Kill the rename-emits-move edge case

Current file classification treats `path_changed or hash_changed` as `modified`
(line 339-341) — correct, keep. But confirm folder classification: a folder rename
changes its children's *paths* but not their parents; children must classify as
`modified` (path update), not `moved`. Logical-parent comparison already guarantees
this — add an explicit test (doc 04).

### 5. Stop re-deriving state the resolver already has

`detect_changes` (line 357) currently:

- `get_all(FileSchema)` + `get_all(FolderSchema)` full docs — still needed in this phase
  for `path`/`hash` per node, but **narrow it**: add
  `structure_repo.get_snapshot_rows(doc_type) -> list[{id, path, hash}]` implemented as a
  triple select (`v:item path v:path`, `v:item hash v:hash`). This is a small, contained
  change here; Phase 3 builds the full lean snapshot on top of it.
- Per-path `read_or_inject_file_id` RPC stays in this phase (Phase 3 removes it) —
  scope discipline: Phase 1 changes *comparison semantics only*.

## Steps (bottom)

1. Add `old_group_id` to `MoveEvent`; update `__str__` of `ChangeSet` (nice for logs).
2. Wire `GroupResolver.load` into `detect_changes` (one call, before classification).
3. Swap physical→logical parents in both `_classify_*` methods.
4. Add `get_snapshot_rows` and use it for the path/hash lookups.
5. Delete `_build_parent_maps` + `_extract_child_id` once nothing references them.
6. Run `tests/unit/parser/analyzer/hierarchy/` — `test_change_detector.py`,
   `test_structure_ops.py`, `test_file_ops.py`, `test_folder_ops.py` must pass unchanged
   (no groups involved ⇒ logical == physical).

## Edge cases

- **Item whose owning group was deleted by the user in-app** between syncs: resolver
  returns the group id that no longer exists → physical parent lookup misses → logical
  parent `None` → would classify as move to FS parent. That is the desired repair
  behavior (re-attach to folder).
- **Two groups claiming the same child** (data corruption): resolver keeps first edge,
  logs warning. Never emit two moves for one id — classification iterates per id, safe.
- **New file created directly into a folder that has a group with the same name**: no
  special case — new files always parent to the physical FS folder; users group them
  afterwards.

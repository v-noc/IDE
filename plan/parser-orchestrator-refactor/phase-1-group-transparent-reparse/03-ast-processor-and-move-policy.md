# Phase 1 / Step 3 — Group-aware code-element sync + one MovePolicy

Files: `collection/ast_processor.py`, `collection/folder_processor.py`,
`collection/file_processor.py`, `repository/structure/structure_repo.py`

## MovePolicy (top)

One policy object answers "should this op emit a move, and to which parent?" for all
three families. Semantics:

```
should_move(item) :=
    desired_logical_parent != current_logical_parent

target_parent(item) :=
    if not should_move:      (no op — keep existing physical edge, grouped or not)
    else:                    desired_logical_parent
                             (item LEAVES its group on a real move; the group lives
                              under the old parent, so keeping membership would lie)
```

Policy choice — *leave group on real move* — is the only self-consistent option:
a structure group under `folder_a` cannot contain a file whose real parent is
`folder_b`; lineage queries (`get_node_lineage`) would produce paths that contradict
the filesystem. Document this in the group docs so it's a product decision, not an
accident. (A future "sticky groups" feature could re-create the group under the new
parent — out of scope.)

## Changes (middle)

### 1. `ast_processor._build_existing_map` (line 65)

Current: `get_children(file_id, exclude_types=[Call, CodeElementGroup, CallGroup])` —
group nodes are excluded from *results* but path traversal goes through them, so
`child_to_parent` loses every group hop (analysis doc §2).

Fix — include groups in the tree, then resolve logically:

```python
existing_tree = await self.repos.structure_repo.get_children(
    file_node.id,
    exclude_types=[CallSchema.__name__, CallGroupSchema.__name__],   # keep CodeElementGroup
)
# build physical child->parent from node.children as today, THEN:
resolver = GroupResolver.from_edges(...)   # local resolver over this file's subtree
existing_map[node.id] = {
    "node": node,
    "parent_id": resolver.logical(node.id),      # logical, not physical
    "physical_parent_id": physical,              # kept for diagnostics
}
# group nodes themselves are NOT added to existing_map (they are not AST-desired nodes,
# so they must never enter the ids_to_delete calculation)
```

Critical detail — **deletion set**: `_determine_sync_operations` (line 250) computes
`ids_to_delete = existing_map − processed_ids`. Group nodes must stay out of
`existing_map` or every sync would delete user groups. Excluding them after using their
edges is the whole point of the two-step above.

### 2. `_determine_sync_operations` move check (line 236)

```python
if existing_parent_id != parent_id:   # both sides now logical → grouped items no-op
    moves_to_execute.append(...)
```

No code change needed beyond the map fix — but add the invariant as a test: a method
inside a `CodeElementGroup` under its class re-syncs with **zero** moves.

### 3. Structure processors consume MoveEvent context

`folder_processor.prepare_batch` / `file_processor.prepare_batch`: nothing structural —
they only see `MoveEvent`s that are now *genuine* moves. Add one guard: if
`move.new_parent_id is None` (unresolvable), skip the move op and log; never emit
`add_triple(None, ...)`.

### 4. `structure_repo.flush_batch` move branch (defense in depth)

Line 235-251 currently deletes whatever parent triple exists and re-adds. Keep, but make
the delete field-scoped per family (it already is) and add a debug log of
`(item, old_group_id)` when `MoveEvent.old_group_id` is set — this is the audit trail
that a group was intentionally dissolved by a real move.

### 5. Call family

Already logical (`diff_calulator._flatten_calls_skipping_groups`). After step 01
extraction, `DiffCalculator` uses the shared helper — verify `CallGroup` children order
is irrelevant (it flattens to a map by id, so yes).

## Steps (bottom)

1. Implement `MovePolicy` (pure function module, ~30 lines) in
   `graph_builder/discovery/move_policy.py`; use it in `_determine_sync_operations` and
   in the change-detector classification (doc 02 step 3) so the rule lives once.
2. Rework `_build_existing_map` per above; add `GroupResolver.from_edges` classmethod
   (build from an in-memory node list instead of a WOQL query — reuse for tests).
3. Guard `None` parents in folder/file processors.
4. Add the audit log in `flush_batch`.
5. Migrate `diff_calulator` to the shared flatten helper (from doc 01 step 4).

## Edge cases

- **Class deleted but its grouped methods remain in AST** (class renamed): methods
  classify as moved to the new class id — group under the dead class is orphaned.
  Orphaned group cleanup: when `ids_to_delete` contains a node, also delete group nodes
  whose *only* children were deleted ids. Implement as a post-pass over the resolver's
  edge map, emit `delete` ops in the same batch.
- **File deleted**: `collector.sync_structure` already appends CodeContent deletes
  (collector.py:77-82); extend the same pass to delete now-empty code-element groups
  physically under that file (`structure_group` groups are NOT deleted when siblings
  remain — only when empty).
- **Group containing both grouped and ungrouped views of the same id** — impossible by
  set semantics in TerminusDB; no handling needed.

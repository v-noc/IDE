# Phase 1 — Group-Transparent Reparse

## Objective

Reparse/resync must treat every group (`StructureGroupSchema`, `CodeElementGroupSchema`,
`CallGroupSchema`) as **transparent**: change detection compares *logical* parents
(groups jumped), and sync never re-parents an item out of a group unless the item
*really* moved on disk (or in the AST).

One sentence invariant:

> **If nothing changed on disk, a resync writes zero move operations — regardless of how
> many groups the user created.**

## Design: physical vs logical parent

```
DB (physical)                         Logical view (groups jumped)
─────────────                         ────────────────────────────
FolderSchema/app                      FolderSchema/app
├── structure_group ─► SG/ui          ├── FileSchema/button.py   (via SG/ui)
│                      ├── file_children ─► FileSchema/button.py
│                      └── file_children ─► FileSchema/input.py  ├── FileSchema/input.py (via SG/ui)
└── file_children ─► FileSchema/api.py└── FileSchema/api.py
```

- **physical parent**: the document holding the direct child edge.
- **logical parent**: first ancestor that is *not* a group. This is what the filesystem
  (or AST) can be compared against.
- The pair `(logical_parent, physical_parent)` is enough for every decision:

| Comparison | Meaning | Action |
|---|---|---|
| logical == FS parent | not moved | none — keep physical (group) edge |
| logical != FS parent | genuinely moved | re-parent; see move policy (doc 03) |

## Work breakdown (top → bottom)

```
phase-1
│
├── 01-group-resolver.md
│   └── new module: graph_builder/discovery/group_resolver.py
│       ├── fetch group docs + edges in ONE lean WOQL query
│       ├── resolve_logical_parent(id) with cycle guard
│       └── owned_group(id) → the group an item currently sits in (or None)
│
├── 02-change-detector-logical-parents.md
│   └── change_detector.py compares logical parents on both sides
│       ├── _build_parent_maps: traverse structure_group edges too
│       ├── MoveEvent gains keep_group context
│       └── modified-only path/qname changes no longer emit moves
│
├── 03-ast-processor-and-move-policy.md
│   ├── ast_processor._build_existing_map: include groups in tree, record
│   │   (logical_parent, physical_parent) per element
│   ├── move suppression: desired parent == logical parent ⇒ no move
│   └── shared MovePolicy for structure + code + calls (align with
│       diff_calulator._flatten_calls_skipping_groups)
│
└── 04-verification.md
    └── unit + e2e tests: resync idempotence with groups at every level
```

## Files touched

| File | Change |
|---|---|
| `graph_builder/discovery/group_resolver.py` | **new** |
| `graph_builder/discovery/change_detector.py` | logical-parent comparison |
| `graph_builder/collection/ast_processor.py` | group-aware existing map + move suppression |
| `graph_builder/collection/folder_processor.py` / `file_processor.py` | consume MoveEvent context |
| `repository/structure/structure_repo.py` (`flush_batch` move branch) | preserve group edge on no-op moves (defense in depth) |
| `graph_builder/call_graph/diff_calulator.py` | extract group-skip helper to shared util |

## Exit criteria

1. Create groups (structure at root, structure nested, code-element on file,
   code-element under class, call group) → run resync twice → all groups intact,
   second resync produces **no move ops and no commits**.
2. Actually move a grouped file on disk → it re-parents according to MovePolicy,
   with exactly one move op.
3. Existing hierarchy unit tests (`tests/unit/parser/analyzer/hierarchy/`) still pass.

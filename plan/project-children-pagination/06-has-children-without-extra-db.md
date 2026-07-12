# 06 — `has_children` without extra DB queries (updated)

## Observation (unchanged)

Documents already store **child IDs** in typed fields. After parsing, **`has_children`** can be **`bool(children)`** (or per-type non-empty sets) **without** another triple query.

## Split-load UX

- **Structure-only first load**: A **file** node may list **non-empty** `class_children` / `function_children` / … IDs in the raw document. The UI can show **expandable** even when **code nodes are not yet loaded**.
- **Lazy fetch**: When the user expands, call the **code subtree** endpoint with **`parent_id`**; merge results into local state or trigger a refetch.

## Avoiding confusion

- Optional flags on API DTOs:
  - **`code_children_loaded`**: `false` until a successful lazy fetch for that file (or parent).
  - Or keep purely client-side state.

This matches: **graph says there are children** (IDs on the node) vs **this response included their documents** (lazy pagination).

## `TreeBuilder`

When only structure is passed in, **code child IDs** on `FileNode` may still be present in the model if the parser preserves them — linking in `TreeBuilder` only attaches nodes **present in `nodes_map`**, so code branches stay **empty** until those nodes are loaded and merged (or a second build pass includes them).

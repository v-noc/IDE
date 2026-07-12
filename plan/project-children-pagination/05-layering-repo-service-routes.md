# 05 — Layering: repository, service, routes (updated)

## `ProjectRepo`

- **`get_structure`**: New method — WOQL type scan limited to **Folder**, **File**, and **StructureGroup** (exact list = product decision). Skip `is_root` folder. Return `(nodes, version?)` like `get_children`.
- **`get_children`**: Retain **full** type list (or restore if temporarily narrowed) for **compatibility**; support **`exclude_types`** as today.

Shared helper (optional): `_fetch_documents_by_types(types, exclude_types, include_commit_id)` to avoid duplicating the WOQL `select` / `read_document` loop.

## `BaseRepo` / `CodeElementRepo`

- Extend **`get_children_by_path`** (or add **`get_descendants_by_path`**) to accept:
  - `max_depth: int | None`
  - `limit: int | None`, `offset: int` **or** cursor handling at service layer
- Build path pattern from **`build_path_field_name`** + **`CODE_ELEMENT_FIELDS`** (and `allowed_path_fields` validation unchanged).
- **`CodeElementRepo`**: Public method e.g. **`get_descendants_paginated(parent_id, child_types, max_depth, limit, offset, …)`** delegating to the extended base primitive; parse with **`parse_code_element_child`**.

## `ProjectService` / `CodeElementService`

- **`get_structure`** → `project_repo.get_structure`.
- **`get_children`** → unchanged forwarding for full graph.
- New: **`get_code_subtree`** (name TBD) → `code_element_repo` paginated/depth method, using project UoW client.

## `project_routes` (and related routers)

- **Option A**: `GET /project/.../structure` (or query flag `?mode=structure`) returning structure-only tree via `TreeBuilder(structure_nodes)`.
- **Option B**: Keep `GET /` behavior until frontend migrates; add parallel routes for structure + lazy code.

**TreeBuilder**: First call with **structure only**; client merges additional node dicts into state or refetches merged list — document chosen approach in frontend plan.

## Shared constants

- Keep **`STRUCTURE_FIELDS`** / **`CODE_ELEMENT_FIELDS`** in **`child_raw.py`** (or extracted module) as single source for path strings and type allowlists.

## Testing seams

- **Unit**: path string for `{1,D}` vs `+`; mock `query` bindings including duplicates for dedupe tests.
- **Integration**: file with deep class/function/call chain; assert `max_depth` and paging boundaries on **`parent_id=file_id`**.

# 07 — Implementation checklist (split-load plan)

## Phase 0 — Product / API decisions

- [ ] Confirm **`get_structure`** type list: `Folder` + `File` only vs include **`StructureGroupSchema`**.
- [ ] Choose HTTP shape: dedicated **`/structure`** route vs query param on existing project GET.
- [ ] Define lazy code route path, auth, and **`compare_to`** behavior.
- [ ] Frontend: state merge strategy (incremental nodes vs refetch structure+code).

## Phase 1 — `ProjectRepo`

- [ ] Implement **`get_structure`** (type-filtered scan, skip `is_root`, optional version).
- [ ] Ensure **`get_children`** restores / maintains **full** type set for **`exclude_types`** compatibility (graph builder, tests).
- [ ] Optional: internal helper shared by `get_structure` and `get_children` to reduce duplication.
- [ ] Remove or gate **debug prints** / timing in production paths.

## Phase 2 — `BaseRepo` + `CodeElementRepo`

- [ ] Extend path helper: **`max_depth`** → `{1,D}` vs **`+`** when `None`.
- [ ] Implement **dedupe**, **stable sort**, **`limit`/`offset`** or **cursor** on descendant results.
- [ ] Add **`get_descendants_paginated`** (or equivalent) on **`CodeElementRepo`** with **`parse_code_element_child`**.
- [ ] Verify WOQL on target server; document fallback if `{n,m}` on grouped choice fails (doc 03).

## Phase 3 — Services

- [ ] **`ProjectService.get_structure`**.
- [ ] **`CodeElementService`** method wrapping new repo API (with `ProjectUoW` / compare client if needed).

## Phase 4 — API routes

- [ ] Wire structure endpoint; wire lazy code endpoint with **`parent_id`**, **`max_depth`**, pagination params.
- [ ] OpenAPI descriptions for pagination and depth semantics.

## Phase 5 — Frontend

- [ ] Initial load: call **`get_structure`** (or new route) instead of full **`get_children`** where appropriate.
- [ ] On expand: fetch code subtree by **`parent_id`**; handle **`has_next_page`** / cursor.

## Phase 6 — Tests

- [ ] **Regression**: `get_children()` full graph and **`exclude_types`** (e.g. exclude `FileSchema`) still pass.
- [ ] **New**: `get_structure` returns only structure types; counts match fixture.
- [ ] **New**: lazy code endpoint respects **`max_depth`** and paging from a **file** `parent_id`.

## Rollout

- [ ] Feature flag optional for new routes.
- [ ] Monitor payload size: structure-only vs historical full `get_children`.

---

## File touch list (expected)

| Area | Files |
|------|--------|
| Project DB scan | `src/backend/app/core/repository/project_repo.py` |
| Code path / depth / page | `src/backend/app/core/repository/base_repo.py`, `code_elements/code_element_repo.py` |
| Services | `project_service.py`, `code_element_service.py` |
| API | `project_routes.py` and/or code-element routes |
| Utils | `repository/utils/child_raw.py` (path constants only if refactored) |

## Risk register

| Risk | Mitigation |
|------|------------|
| WOQL rejects `{n,m}` on grouped choice | Fallbacks in doc 03 |
| Duplicate path bindings | Dedupe by `@id` |
| UI shows empty code until expand | Document; optional `code_children_loaded` |
| Graph builder needs full list | Keep **`get_children`** for orchestration |

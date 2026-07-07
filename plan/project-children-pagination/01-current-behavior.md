# 01 — Current behavior

## `ProjectRepo.get_children`

Implementation: `src/backend/app/core/repository/project_repo.py`.

**Typical / intended production shape** (may vary in local experiments):

1. Builds a WOQL query that selects every document whose `rdf:type` is one of several schema types, minus `exclude_types`.
2. Executes `read_document` for each matching URI and collects bindings.
3. Skips the synthetic root folder (`FolderSchema` with `is_root == "true"`), created at project setup.
4. Maps each raw document through `parse_structure_child` (`src/backend/app/core/repository/utils/child_raw.py`).
5. Optionally returns the data version when `include_commit_id=True`.

There is **no** path traversal from a single project anchor and **no** pagination. The result set scales with **whichever types are included** (full graph vs structure-only if types are narrowed).

## How the tree is built

`project_routes` loads `children` and passes them to `TreeBuilder` (`src/backend/app/core/builder/tree_builder.py`):

- Child document IDs come from typed set fields on each document; linking is in memory by ID.
- Roots are nodes not referenced as a child of another node **in the loaded set**.

With a **split load**, the first paint may intentionally pass **only structure nodes** into `TreeBuilder`; code nodes appear after **lazy fetches** keyed by `parent_id` (see [00-split-load-strategy.md](./00-split-load-strategy.md)).

## `StructureRepo.get_children(parent_id)` and `CodeElementRepo.get_children(parent_id)`

These use `BaseRepo.get_children_by_path` with a **known start URI** and `(field1|field2|…)+` — the right place for **depth-bounded** and **paginated** descendant queries for code (plan: extend here rather than inventing a project-wide path anchor).

## Contrast with planned `get_structure`

- **`get_structure`**: deliberate **small type set** (folder/file/(group)) — same **scan** style as `get_children`, different **scope**.
- **`get_children`**: keep for **full graph** or `exclude_types` for tools and backward compatibility.

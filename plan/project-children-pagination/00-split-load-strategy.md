# 00 — Chosen strategy: structure first, lazy code by parent

This supersedes the earlier idea of **paginating monolithic `ProjectRepo.get_children`** with path queries from an imaginary project anchor.

## Problem with paging `get_children` alone

- The **project document** in the meta DB is not the root of the analysis graph in the project TerminusDB.
- In the project DB, **tree roots** are discovered by “not referenced as anyone’s child” (`TreeBuilder` semantics). There is **no single `start` URI** for a WOQL path that means “the whole project.”
- A flat **type sweep** (`rdf:type` ∈ … + `read_document`) is easy for “all folders/files” or “everything,” but **depth and cursors** do not map cleanly onto that query without extra machinery.

## Preferred approach (two-phase loading)

### Phase A — Initial structure load: `get_structure`

- **New** repository method (name TBD; working name `get_structure`) on `ProjectRepo` (or equivalent).
- Loads **only structural** documents: at minimum **Folder** and **File**; include **StructureGroup** if the product tree treats groups as part of the folder/file shell (matches `STRUCTURE_FIELDS` / `TreeBuilder` expectations).
- Implementation: same pattern as today’s **type-filtered document scan** (no path-from-root required). Dataset is smaller than “all code,” so full scan per request is more acceptable.
- Still skip the synthetic `is_root` theme folder row if that remains the rule.
- Optional: `include_commit_id` / version for ETags, mirroring `get_children`.

### Phase B — Lazy code load: `CodeElementRepo` (+ related repos if needed)

- **New or extended** API on `CodeElementRepo` (`src/backend/app/core/repository/code_elements/code_element_repo.py`): fetch **functions / classes / calls / groups** as descendants of a **known `parent_id`** (typically a **file**, or a class/function when drilling in).
- Uses existing **path-based** primitives (`BaseRepo.get_children_by_path` pattern) with a choice over **`CODE_ELEMENT_FIELDS`** (and any call-specific fields already used elsewhere), i.e. the same edge vocabulary as `build_path_field_name`.
- **Depth**: express with TerminusDB path **times** on the grouped choice, e.g. `(field1|field2|…){1,D}` — see [path query reference](https://terminusdb.org/docs/path-query-reference-guide/) and doc 03.
- **Pagination**: `limit` / `offset` or opaque **cursor** after a **stable sort** (e.g. by `@id`) and **deduplication** (paths can yield duplicate URIs). Prefer documenting worst case (post-filter slice) vs BFS paging in doc 03.

### `get_children` and `exclude_types`

- Keep **`get_children`** for **backward compatibility**: full graph (or full graph minus `exclude_types`) for graph rebuild, tests, compare mode, and any batch jobs that still need one flat list.
- Do **not** rely on `get_children` as the primary API for the dashboard’s first paint; use **`get_structure`** + lazy code fetches instead.

## Why this is maintainable

- **Structure** and **code** concerns stay in the repos that already own those edges (`project_repo` / `structure_repo` patterns vs `code_element_repo`).
- Path depth and pagination apply only where a **real anchor** exists: **`parent_id`**.

## Frontend / `TreeBuilder` note

- First response may contain only structure nodes; **code slots** under files may be **empty in the built tree** until the client requests code for that `parent_id`.
- **Has-children** for UX can still use **stored child IDs** on documents already loaded (doc 06): a file can show “expandable” if `class_children` / `function_children` / … are non-empty without an extra DB round-trip, while actual **node payloads** load on demand.

# 04 — API and response contracts (updated)

## Two entry points (conceptual)

### 1) Initial structure — `get_structure` (service/repo)

- **Purpose**: First paint of the project tree shell (folders, files, structure groups as needed).
- **Query params** (optional): `exclude_types`, `include_commit_id` / version — mirror `get_children` ergonomics where useful.
- **Response**: List of parsed structure nodes (same parsing as today for those types) + optional version.

No **`parent_id`** required: this is a **scoped type sweep**, not a path from root.

### 2) Lazy code — code subtree by `parent_id`

- **Purpose**: Load functions/classes/calls/groups under a **specific** node (usually a **file**).
- **Query params** (suggested):
  - `parent_id` (required): anchor document ID.
  - `max_depth` (optional): maps to path `{1,D}`; omit = same as unlimited `+`.
  - `limit`, `offset` **or** `cursor` + `page_size` for pagination.
  - `child_types` (optional): narrow edges, reusing the same strings as `CodeElementRepo.get_children` today.

- **Response**:
  - `nodes`: parsed code elements (and groups as included).
  - `has_next_page`, `next_cursor` (if using cursors).
  - `max_depth_applied` (echo for debugging).

Expose via **dedicated route(s)** under project or code-element API; avoid overloading **`GET /` project** until behavior is agreed.

## Backward-compatible full graph

- **`get_children`** on **`ProjectRepo`** / **`ProjectService`**: unchanged contract for callers that need **all** types (minus `exclude_types`), including graph rebuild and tests.

## Compare (`compare_to`) mode

- **Structure**: same as today if compare swaps the project DB client — document whether version/compare applies to `get_structure`.
- **Lazy code**: either duplicate params against compare client or return `400` until implemented symmetrically.

## Errors

- `400`: missing `parent_id` on lazy code endpoint, invalid `max_depth`, bad cursor.
- `404`: parent document not found (optional explicit check).

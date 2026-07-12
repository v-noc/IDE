# 03 — TerminusDB path expressions and depth (updated focus)

Reference: [TerminusDB path query reference guide](https://terminusdb.org/docs/path-query-reference-guide/).

## Where path depth applies in the new plan

| Load | Mechanism | Depth / pagination |
|------|-----------|-------------------|
| **Structure (`get_structure`)** | Type-filtered `rdf:type` + `read_document` (like today’s sweep, fewer types) | Usually **not** path-based; volume is smaller. Optional future: cap by querying from known folder IDs only. |
| **Code (lazy)** | `CodeElementRepo` from **`parent_id`** | **Path** over **`CODE_ELEMENT_FIELDS`** with `+` (unlimited) or **`{1,D}`** (max depth); then **sort, dedupe, slice** or cursor. |

## Code-edge vocabulary

Use the same fields as today’s code path building (`child_raw.py`):

- `function_children`, `class_children`, `call_children`, `code_element_group`, `call_group`

`build_path_field_name([], CODE_ELEMENT_FIELDS, …)` yields a grouped choice for WOQL `.path("v:start", pattern, "v:child")`.

## Depth as `{n,m}` on the grouped path

- **Unlimited descendants** (current behavior): append `+` to the choice group, e.g. `(a|b|c)+`.
- **Bounded depth `D`**: append `{1,D}` — e.g. `(a|b|c){1,D}` for at least one hop and at most `D` hops from **`parent_id`** (does not include the parent document itself).

**Verify** on your TerminusDB version that `{n,m}` is accepted on a **parenthesized choice**; if not, use fallbacks documented previously (repeated path segments or layered BFS in application code).

## Pagination after path results

Path queries can return **duplicate** bindings for the same URI via different paths — **dedupe by `@id`** before sorting.

Then:

1. **Stable sort** (e.g. lexical `@id`).
2. **`limit` / `offset`** or encode **`last_id`** in an opaque cursor for the next page.

For very large subtrees, consider **BFS by depth layer** with a cursor that includes `(depth, last_id)` instead of materializing the full reachable set (trade-off: more round-trips, bounded memory).

## Anchors — simplified

- **Structure scan**: no path anchor; types define the set.
- **Code lazy load**: **`parent_id`** is the anchor (must be a valid document ID in the project DB, typically a file or an already-loaded code node).

## Type filtering

Restrict `rdf:type` on `v:child` to the code-related schema types you want in the response (function, class, call, groups), aligned with `parse_code_element_child` and related parsers.

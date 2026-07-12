# 02 — Requirements and constraints (updated)

## Goals

1. **Fast initial project tree**: load **structure only** via **`get_structure`** (folders, files, and structure groups if the tree requires them) without pulling every function/class/call into memory.
2. **Lazy code loading**: load functions/classes/calls/groups **from a known `parent_id`** (e.g. file) with **optional `max_depth`** (TerminusDB path `{n,m}` on grouped code edges — [path reference](https://terminusdb.org/docs/path-query-reference-guide/)) and **pagination** (limit/offset or cursor).
3. **Backward compatibility**: **`get_children`** (with **`exclude_types`** as today) remains available for full-graph consumers: graph builder orchestration, tests, compare mode, log pipelines, etc.
4. **Maintainability**: structure scanning stays in **`ProjectRepo`**; path+depth+paging for code stays in **`CodeElementRepo`** / **`BaseRepo`** extensions, reusing **`CODE_ELEMENT_FIELDS`** and **`build_path_field_name`**.

## Non-goals (initial phase)

- Depth-paginating **only** `get_children` from a non-existent “project graph root” URI (replaced by split load; see [00-split-load-strategy.md](./00-split-load-strategy.md)).
- Guaranteeing a global sort over the **entire** project graph without defining ordering for **paginated code** slices (define per endpoint).

## Hard constraints

- **Lazy code**: responses must be clear whether **child documents** are omitted by pagination vs absent in the graph (see doc 06).
- **Compare mode**: if compare returns two trees, lazy code endpoints must either accept **compare** context (branch/ref) consistently or document limitations.
- **`TreeBuilder`**: may run on **structure-only** lists first; merging in code nodes later is a **client or orchestration** responsibility unless a server-side merge helper is added later.

## Success criteria

- Dashboard (or API client) can render **folder/file tree** without loading all code elements.
- Expanding a file (or similar) can fetch **paged, depth-limited** code subgraphs anchored at **`parent_id`**.
- Existing callers of **`get_children`** / **`exclude_types`** continue to work for full-graph scenarios.

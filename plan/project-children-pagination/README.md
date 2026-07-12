# Project tree loading: structure + lazy code (plan)

This folder is a **review-oriented implementation plan**. The **recommended direction** is documented in **[00-split-load-strategy.md](./00-split-load-strategy.md)**:

1. **`get_structure`** — initial load: folders/files (and structure groups if required), via a **type-filtered scan** on the project DB.
2. **Lazy code load** — **`CodeElementRepo`** (from a **`parent_id`**) with **TerminusDB path depth** (`{n,m}` on grouped code edges) and **pagination**.

Paginating **only** `get_children` as a single path from a project root is **deprioritized** (no natural anchor in the DB). `get_children` remains useful as a **full-graph** (or `exclude_types`) API for compatibility.

## How to read these docs

| File | Purpose |
|------|---------|
| [00-split-load-strategy.md](./00-split-load-strategy.md) | **Start here** — chosen two-phase approach and rationale |
| [01-current-behavior.md](./01-current-behavior.md) | What the code does today |
| [02-requirements-and-constraints.md](./02-requirements-and-constraints.md) | Goals aligned with split load + compatibility |
| [03-terminusdb-path-and-depth.md](./03-terminusdb-path-and-depth.md) | Path syntax; **primary use: code subtree from `parent_id`** |
| [04-api-and-contracts.md](./04-api-and-contracts.md) | Routes/contracts for structure vs code lazy endpoints |
| [05-layering-repo-service-routes.md](./05-layering-repo-service-routes.md) | `ProjectRepo` vs `CodeElementRepo` / `BaseRepo` |
| [06-has-children-without-extra-db.md](./06-has-children-without-extra-db.md) | Child IDs on nodes + lazy UI |
| [07-implementation-checklist.md](./07-implementation-checklist.md) | Ordered steps for the split design |

## External reference

- [TerminusDB path query reference](https://terminusdb.org/docs/path-query-reference-guide/) — sequence, choice, `+`, `*`, `{n,m}`, backward `<field`.

## Terminology

- **Structure slice**: Folders, files, (optional) structure groups — loaded without traversing from a single graph root document.
- **Code subtree**: Descendants of a **concrete document** (`FileSchema` / …) along **code** edges (`function_children`, `class_children`, …), with optional **max depth** and **pages**.
- **`get_children` (project)**: Flat list of many schema types for **full tree materialization**; keep for jobs/tests/compare, not the only dashboard entry point.

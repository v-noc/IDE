# Phase 4 — Repository & Service Reorganization

## Objective

After Phase 2, repos are commit-free. This phase makes the layering explicit and
uniform, replaces `print`-and-`None` error handling with typed errors, and removes the
duplication that makes every new node type a copy-paste exercise.

## Target layering (dendrogram, top → bottom)

```
api/v1/* routes                      thin: parse request → service → response schema
│
├── services/                        use-case logic; owns SyncWriteBatch per action
│   ├── one service per aggregate (structure, code_element, call, group, project, …)
│   └── never build WOQL, never touch AsyncClient directly
│
├── repository/
│   ├── write_batch.py               (Phase 2) the only commit path
│   ├── queries/                     NEW — read-side query builders
│   │   ├── children.py              path/descendant queries (from BaseRepo.get_children_by_path)
│   │   ├── snapshot.py              lean snapshots + edge triples (Phase 3)
│   │   └── lineage.py               get_node_lineage etc.
│   ├── repos/                       per-aggregate: typed read API + stage helpers
│   │   └── (structure, code_element, call, group, project, document, log, test)
│   └── mapping.py                   raw dict ⇄ Node ⇄ Schema converters (from child_raw.py
│                                    parse_* + BaseRepo._to_node/_to_schema)
│
└── db/                              client, mixins, scoping — unchanged surface
```

`BaseRepo` (439 lines) dissolves into: `queries/` (reads), `write_batch.py` (writes),
`mapping.py` (conversion). What remains of a "repo" is a thin façade binding the three
for one aggregate — easy to test, impossible to hide a stray commit in.

## Error model

```
app/utils/exceptions.py grows a hierarchy:
    VnocError
    ├── DbError          (wraps DatabaseError/InterfaceError; carries query summary)
    ├── NotFoundError    (id, type)
    ├── ConflictError    (data-version mismatch after retry)
    ├── DriverError      (from DriverRpcError; carries method, file)
    └── SyncError        (session id, phase, per-file failures list)
```

Rules:
- repos/queries **raise**; they never return `None`/`False`/`[]` to signal failure
  (empty results are `[]`, failures are exceptions — today these are conflated,
  e.g. base_repo.py:74-82 returns `[]` on connection error, which upstream treats as
  "file has no children" and then deletes elements!).
- services translate to HTTP/JSON-RPC errors at the boundary
  (`api/json_rpc/error.py` pattern already exists — extend it).
- `print(` is banned in `app/core` (CI grep gate, started in Phase 2).

## Docs

- `01-base-repo-split.md` — mechanical decomposition plan with method-by-method map.
- `02-error-handling-and-logging.md` — exceptions, logging fields, the silent-failure
  audit list.
- `03-service-conventions.md` — service API shape, group service dedup, schema decisions
  (code_position flattening).
- `04-verification.md`

## Depends on

Phase 2 (repos already commit-free). Can overlap Phase 3 — coordinate on
`queries/snapshot.py` which Phase 3 introduces.

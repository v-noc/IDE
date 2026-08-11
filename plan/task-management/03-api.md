# 03 — API

The HTTP surface, in the existing house pattern. Nothing architecturally new:
one routes file, one service, two repos, registered where everything else is
registered.

## Files & registration

```
src/backend/app/core/model/tasks.py                  TaskNode · TaskAnchor · BoardNode · BoardColumn
src/backend/app/core/model/schemas/task_schema.py    TaskSchema · TaskAnchorSchema · BoardSchema · …
src/backend/app/core/repository/task_repo.py         TaskRepo(BaseRepo[TaskNode, TaskSchema])
src/backend/app/core/repository/board_repo.py        BoardRepo(BaseRepo[BoardNode, BoardSchema])
src/backend/app/core/services/task_service.py        TaskService (all rules live here)
src/backend/app/api/v1/task_routes.py                FastAPI router
```

- Repos registered in `Repositories.__init__` (`core/repository/__init__.py`)
  next to `document_repo` / `conversation_repo`.
- Router registered in `api/root.py`:
  `router.include_router(task_routes.router, prefix="/tasks", tags=["tasks"])`.
- DI provider `get_task_service` in `api/dependencies.py`, mirroring
  `get_document_service`.
- Board bootstrap: `TaskService.get_board` creates the default board (5
  columns, Backlog/To do/In progress/In review/Done, `is_done` on Done) on
  first read — same lazy-init spirit as `FolderSchema.create_init_folder`.

## Endpoints

All under the project-scoped client (db + branch), like every other v1 route.

> **Correction (2026-07-18, from implementation):** task ids are
> `TaskSchema/{uuid}` — they contain a `/`, so `{id}` **path params in this
> table do not route** (Starlette matches one segment; every per-task call
> 404s). Ids travel as **query params**, the grammar `document_routes.py`
> already uses (`document_id: str = Query(...)`). Read the table's
> `/tasks/{id}/x` rows as `POST /tasks/x?task_id=…`. Full diagnosis and the
> rejected alternatives: `fixes/02-task-routes-404.md`.

| Method & path | Body / params | Does |
|---|---|---|
| `GET /tasks/board` | `scope_node_id?` | Board + columns + tasks with derived fields (one payload; boards are small in v1). **Scope follows the commits grammar** (`versioning/commits.py`): param absent or a `ProjectSchema/` id → all tasks; otherwise → tasks with ≥1 anchor on the node **or any node in its subtree** (membership resolved server-side over the existing children sets). Response echoes `scope` + per-scope open/hot counts for the board header |
| `POST /tasks/` | title, task_type, priority, description?, labels?, status?, anchors?, subtask_of? | Create; mints `VN-<n>`; ranks at column top; optional initial anchors + parent (the modal's one-shot create) |
| `PATCH /tasks/{id}` | any of title/description/task_type/priority/labels | Field updates; system note appended for type/priority changes |
| `POST /tasks/{id}/move` | status, rank | Column + order in one call; validates column id; rebalances on midpoint exhaustion |
| `DELETE /tasks/{id}` | — | Delete + unlink from all parents/dependents (one commit batch) |
| `POST /tasks/{id}/subtasks` | child_id (or inline create payload) | DAG edge add; **cycle check**; inline payload = create-and-link (suggested-subtasks path) |
| `DELETE /tasks/{id}/subtasks/{child_id}` | — | Edge remove; child never deleted |
| `POST /tasks/{id}/blocked-by` · `DELETE …/{blocker_id}` | blocker_id | Dependency edges, same cycle guard |
| `POST /tasks/{id}/anchors` | node_id | **Idempotent** add (existing → no-op); snapshot qname/kind; refuse if node absent |
| `DELETE /tasks/{id}/anchors` | node_id (query) | **Idempotent** remove, keyed by node — never by index. The add/remove pair is what every toggle surface calls |
| `POST /tasks/{id}/anchors/move` | from_node_id, to_node_id | Atomic transfer: remove + add with fresh snapshot + one system note, one commit. Source may be dead — **re-anchor is this endpoint**; target must be live |
| `GET /tasks/anchor-summary` | — | The convergence payload (02); cached |
| `GET /tasks/re-anchor-candidates` | qname, kind | Ranked live-node candidates for the picker |
| `POST /tasks/{id}/notes` | text | User note |
| `PATCH /tasks/board` | columns[] | Rename/recolor/reorder columns; delete requires `move_to`; `is_done` editable. **The backlog column is protected**: rename/recolor only — delete or un-flagging `is_backlog` is refused; `is_backlog`+`is_done` on one column is refused (01) |

Not endpoints: filtering and **search** (title/key/labels/anchor qnames —
04's one search box) are client-side in v1 — the board payload is already
complete, and the List view is the same payload projected differently, so no
list endpoint exists either. A `?filter=`/`?q=` query param is a seam for
when boards outgrow one payload. **Scope is the exception and is
server-side**: subtree membership is a graph fact the client can't be trusted
to hold completely (partially loaded trees), and the commits endpoint already
settled this split — scope on the wire, cosmetic filters in the client.

## Validation sentences (service-level, HTTP 409/422)

The service refuses with sentences the UI can show verbatim, grouper-style:

- Cycle: `"VN-11 already contains VN-9 through VN-12 — adding this edge would create a cycle."`
- Dead anchor: `"FunctionSchema/x9 does not exist on this branch — pick a live node."`
- Column delete: `"'In review' still has 3 tasks — choose a column to move them to."`
- Backlog column: `"'Backlog' is the board's backlog column — it can be renamed, not deleted."`
- Bad move target: `"Unknown column 'sprint-2' — the board has: backlog, todo, …"`

## Derived fields on the wire

`GET /tasks/board` task objects carry (never accepted on writes):

```
blocked: bool                      # any blocker open
subtask_progress: {done, total}    # closure-deduped
anchors[i].is_resolved: bool       # batched existence check
subtasks[i].shared: bool           # parent count > 1
blocks: [task_id]                  # reverse edges, service-computed
```

## Caching, commits, events

- `GET /tasks/board` and `GET /tasks/anchor-summary`: `@cache(expire=DEFAULT_TTL)`
  + explicit invalidation on every task write (per-project key bump). The
  board cache key includes `scope_node_id` — each scope is its own entry, all
  dropped by the same project-level bump.
  > **Correction (2026-07-18):** `@cache` also stamps
  > `Cache-Control: max-age=86400` on the response — the **browser** then
  > serves stale boards to every react-query refetch for 24h, even with the
  > server cache disabled. v1 drops the decorator from both task GETs;
  > if caching returns, task responses must send `no-store`. See
  > `fixes/01-board-cache-staleness.md`.
- Every write is **one commit batch** with a message the versioning UI can
  show (`"task: VN-12 moved to In progress"`) — task history rides the
  existing commits view for free, and run-level undo (agent-v3 pattern) stays
  possible when agent tools arrive.
- After invalidation the service emits `tasks.changed` /
  `tasks.summary_changed` over the existing socket layer; payload = project id
  only (clients refetch; no state over the wire).

## Tests

House pattern (`tests/unit`, `tests/e2e`): service-level unit tests for the
cycle validator, closure dedupe, LexoRank rebalance, VN-counter atomicity;
HTTP tests for the T1 demo gate (mock board round-trip, refused cycle, move).

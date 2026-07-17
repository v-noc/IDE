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

| Method & path | Body / params | Does |
|---|---|---|
| `GET /tasks/board` | — | Board + columns + all tasks with derived fields (one payload; boards are small in v1) |
| `POST /tasks/` | title, task_type, priority, description?, labels?, status?, anchors?, subtask_of? | Create; mints `VN-<n>`; ranks at column top; optional initial anchors + parent (the modal's one-shot create) |
| `PATCH /tasks/{id}` | any of title/description/task_type/priority/labels | Field updates; system note appended for type/priority changes |
| `POST /tasks/{id}/move` | status, rank | Column + order in one call; validates column id; rebalances on midpoint exhaustion |
| `DELETE /tasks/{id}` | — | Delete + unlink from all parents/dependents (one commit batch) |
| `POST /tasks/{id}/subtasks` | child_id (or inline create payload) | DAG edge add; **cycle check**; inline payload = create-and-link (suggested-subtasks path) |
| `DELETE /tasks/{id}/subtasks/{child_id}` | — | Edge remove; child never deleted |
| `POST /tasks/{id}/blocked-by` · `DELETE …/{blocker_id}` | blocker_id | Dependency edges, same cycle guard |
| `POST /tasks/{id}/anchors` | node_id | Snapshot qname/kind; refuse if node absent |
| `DELETE /tasks/{id}/anchors/{index}` | — | Remove by position (anchors are an ordered list) |
| `POST /tasks/{id}/anchors/{index}/re-anchor` | node_id | Replace + refresh snapshot + system note |
| `GET /tasks/anchor-summary` | — | The convergence payload (02); cached |
| `GET /tasks/re-anchor-candidates` | qname, kind | Ranked live-node candidates for the picker |
| `POST /tasks/{id}/notes` | text | User note |
| `PATCH /tasks/board` | columns[] | Rename/recolor/reorder columns; delete requires `move_to`; `is_done` editable |

Not endpoints: filtering (labels/type/priority/anchor search) is client-side in
v1 — the board payload is already complete. A `?filter=` query param is a seam
for when boards outgrow one payload.

## Validation sentences (service-level, HTTP 409/422)

The service refuses with sentences the UI can show verbatim, grouper-style:

- Cycle: `"VN-11 already contains VN-9 through VN-12 — adding this edge would create a cycle."`
- Dead anchor: `"FunctionSchema/x9 does not exist on this branch — pick a live node."`
- Column delete: `"'In review' still has 3 tasks — choose a column to move them to."`
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
  + explicit invalidation on every task write (per-project key bump).
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

# Fix 02 — Every per-task endpoint 404s: ids contain `/`

## Symptom

Nothing that targets an existing task persists:

- Board/list drag to another column → optimistic move, then silent rollback.
- Title edit on blur → no change. Notes → nothing. Re-anchor → nothing.
- No error appears anywhere (see "Surface errors" below).

Create (`POST /tasks/`) and reads (`GET /tasks/board`) work — which is why
the feature *looks* half-alive: tasks exist, but are frozen at birth.

## Root cause

Task ids are minted as `TaskSchema/{uuid4}` (`task_service.py:102`) — the
house id format, **which contains a slash**. The frontend interpolates the
raw id into the URL path:

```ts
// services/tasks/api.ts:83
api(`${API_ROUTES.TASKS}/${taskId}/move…`)
// → POST /api/v1/tasks/TaskSchema/3f2c…/move
```

Starlette path params (`/{task_id}/move`, `task_routes.py:118`) match a
**single** path segment. `TaskSchema/3f2c…/move` is three segments — no
route matches → **404 Not Found** for every one of:

`PATCH /tasks/{id}` · `POST /tasks/{id}/move` · `DELETE /tasks/{id}` ·
`/{id}/subtasks…` · `/{id}/blocked-by…` · `/{id}/anchors…` ·
`/{id}/anchors/{i}/re-anchor` · `/{id}/notes`

The react-query mutations then fire `onError` → optimistic rollback
(`useTasks.ts:109-113`) → "the card snaps back, there is no update".

**Why tests didn't catch it:** `tests/unit/service/test_task_service.py`
tests the service layer directly; no HTTP test ever sent a real task id
through the router. (03's test section asked for HTTP tests of the T1 demo
gate — add them with this fix.)

**Plan correction:** 03's endpoint table specified `/tasks/{id}` without
flagging the slash. The existing house grammar already solved this —
document ids travel as query params (`document_routes.py:59`:
`document_id: str = Query(...)`) precisely because house ids embed `/`.
03 now carries a correction note pointing here.

## Fix (recommended): ids as query params, house-style

Backend — replace every path `{task_id}` with a query param:

```python
@router.post("/move")
async def move_task(
    task_id: str = Query(...),
    request: MoveTaskRequest, ...
)
```

Route shapes become: `PATCH /tasks` · `POST /tasks/move` ·
`POST /tasks/subtasks` (child in body) · `POST /tasks/anchors` etc. — flat
paths, ids in query/body, exactly like documents. The anchor index params
disappear anyway once anchors are node-keyed ([fix 05](05-unbuilt-plan-surfaces.md)).

Frontend — `services/tasks/api.ts` moves `taskId` into `projectQs(...)`
alongside `project_id`. One mechanical pass; the hook layer doesn't change.

### Rejected alternatives

- **`{task_id:path}` converter** — greedy: in `/{task_id:path}/move` it
  swallows `/move` too. Only works for suffix-less routes; halfway fixes.
- **`encodeURIComponent(taskId)` client-side** — `%2F` in paths survives
  Starlette but is normalized/rejected by common proxies (nginx
  `merge_slashes`, some CDN configs). Fragile grammar; the query param is
  the pattern the rest of the app already trusts.

## Surface errors while you're in here

Every mutation failure today is invisible — `onError` only rolls back the
cache. 03 designed the validation messages to be shown verbatim ("VN-11
already contains VN-9 … would create a cycle"). Add a shared `onError` in
the task mutations (`useTasks.ts`) that toasts
`error.response.detail ?? "Task update failed"` via the app's toast/sonner
util. Without this, the *next* silent failure costs another debugging
session.

## Verify

- HTTP test: create → move → PATCH title → add note → add subtask, all via
  the router with real `TaskSchema/…` ids (the T1 demo-gate test 03 asked
  for).
- UI: drag `To do → In progress`, hard-refresh, the card is still in
  In progress and its activity reads "Moved to In progress".

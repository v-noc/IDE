# Fix 01 — Board staleness: create/move don't show until a page refresh

## Symptom

- Create a task → the board doesn't show it; a full page refresh does.
- Drag a card to another column → it moves, then **snaps back** when the
  refetch settles (this symptom is shared with [fix 02](02-task-routes-404.md)
  — both causes are real and independent).
- Node badges / open counts lag behind reality.

## Root cause

`GET /tasks/board` and `GET /tasks/anchor-summary` are wrapped in
`@cache(expire=DEFAULT_TTL)`:

- `src/backend/app/api/v1/task_routes.py:71-76` and `:252-257`
- `DEFAULT_TTL = 24 * 60 * 60` — **24 hours** (`app/core/cache_setup.py:18`)

Two failure layers, and only the first one is environment-dependent:

1. **Server cache (prod-only landmine).** With `ENABLE_CACHE=true` (Redis),
   the response is cached server-side for 24h and **no task write ever
   invalidates it**. Plan 03 explicitly required "explicit invalidation on
   every task write (per-project key bump)" — the service emits socket events
   in `_emit_changed` (`task_service.py:40-57`) but never clears the cache.
   In dev this layer is a no-op (`ENABLE_CACHE` defaults to `False` →
   `NoOpBackend` always misses).

2. **Browser cache (the dev symptom).** fastapi-cache sets response headers
   on **every** response, including NoOp-backend misses
   (`fastapi_cache/decorator.py:201`):

   ```
   Cache-Control: max-age=86400
   ETag: W/<hash>
   ```

   So the browser's HTTP cache holds `GET /api/v1/tasks/board?project_id=…`
   for 24 hours. React-query's `invalidateQueries` dutifully refetches — and
   `fetch()` serves the **stale cached body without hitting the server**.
   The query key (`useTasks.ts:9-20`) includes branch/ref, but the *URL*
   only varies by `project_id`, so the browser cache key never changes.
   A page reload forces revalidation (`If-None-Match` → NoOp backend
   recomputes → fresh body), which is exactly why "refresh fixes it".

This also explains why the **optimistic move reverts** even when the move
would succeed: `useMoveTask.onSettled` invalidates → refetch → browser
returns the pre-move payload → the card jumps back.

## Fix

### v1 (do now): drop the decorator from task reads

Remove `@cache(expire=DEFAULT_TTL)` from both task GETs in
`task_routes.py`. The board payload is one small query over a per-project
task set — correctness beats a cache we can't invalidate. The socket events
plus react-query are the freshness mechanism the plan intended.

### v2 (when caching is actually wanted): cache with a bump key

If board reads ever get expensive (anchor resolution over many nodes):

- Add a per-project **version counter** to the cache key: bump it in
  `_emit_changed` (one Redis `INCR`), include it in a custom key builder for
  task routes. All scopes/branches drop together, matching 03's design.
- Either way, task responses must send `Cache-Control: no-store` (or fork the
  decorator's header behavior) — a server-side cache must never leak a 24h
  `max-age` to the browser for data with sub-second freshness requirements.

## House-wide note (out of this plan's scope, worth a ticket)

Every `@cache(expire=DEFAULT_TTL)` endpoint in the app ships the same
`max-age=86400` browser header — e.g. `document_routes.py:106`. Documents
tolerate it better because their reads go through different UI paths, but the
same "edit → stale read" hazard exists anywhere react-query invalidation
assumes the network returns fresh data. Audit separately; don't fix here.

## Verify

1. DevTools → Network, "Disable cache" **off**. Create a task.
2. The board refetch after `invalidateQueries` must hit the server (status
   200 from network, not "(disk cache)") and contain the new task.
3. Drag a card across columns; after the refetch settles the card stays.

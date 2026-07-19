# Task Management — Implementation Fixes (found 2026-07-18)

The T1–T3 implementation on `agent_harness` ships a working data model and a
half-working UI. Testing against the approved design surfaced three behavior
bugs and one large scope gap. **None of the missing detail-panel content was
un-planned — 05 specifies every section in the mock.** What happened is: two
real bugs make the shipped half feel broken, and most of T3's UI was skipped.

Read these in order — 01 and 02 are the bugs that make everything else look
broken; fix them before judging any UI work.

| # | Symptom (as reported) | Root cause | Was it in the plan? |
|---|---|---|---|
| [01](01-board-cache-staleness.md) | "After creating I have to refresh to see the change" | `@cache` on `GET /tasks/board` sends `Cache-Control: max-age=86400` — the **browser** serves the stale board to every react-query refetch for 24h | Partially. 03 required server-side invalidation on writes (skipped); the browser-header angle was missed by the plan too → now added |
| [02](02-task-routes-404.md) | "Update from column to next is not working, there is no update" | Task ids are `TaskSchema/{uuid}` — the `/` breaks `/tasks/{task_id}/move` path matching → **every per-task endpoint returns 404**; optimistic UI rolls back silently | Plan bug. 03's endpoint table wrote `/tasks/{id}` without flagging that house ids embed `/`; the house grammar (document_routes) uses query params for exactly this reason → 03 corrected |
| [03](03-anchorless-create-and-new-task-here.md) | "It always creates a task, no anchor node" | Three causes: `NewTaskModal` only mounts inside the Tasks tab (canvas "New task here" no-ops); board `+ New task` never pre-fills the active node; no post-create anchor path exists anywhere | In the plan (04, 05, 06). Modal mount location was unspecified — now specified |
| [04](04-detail-panel-gaps.md) | "The implemented version is small and forgot subtasks and other things" | The panel shipped ~30% of 05's spec: no status/priority editing, no description, no labels, no created/updated, no add-anchor, no subtask checkboxes/add/suggest, no dependencies section. Plus: "Focus on canvas" enters the lens with **no exit** | Fully in the plan (05). Skipped, not un-planned |
| [05](05-unbuilt-plan-surfaces.md) | (general "it's a mess") | T3/T4 remainder: scope pill, node popover, Blockers section, idempotent anchors + `anchors/move`, mutation-error toasts | Fully in the plan (README decisions 8–9, 02, 04, 05) |

## Fix order

1. **02 first** (routes 404) — it gates every mutation the UI already has.
2. **01 second** (cache) — one-line removal + a follow-up invalidation task.
3. **03** (anchor creation flow) — restores the feature's reason to exist:
   without anchors there are no hot nodes.
4. **04** (detail panel) — pure UI build against endpoints that will now work.
5. **05** (remaining surfaces) — T3/T4 as planned.

## Verification gate (repeat the reported flows)

- Create a task from the board → it appears on the board **without refresh**.
- Drag a card `To do → In progress` → it stays after the refetch settles, and
  the card's activity shows "Moved to In progress".
- Right-click a canvas node → *New task here* → modal opens **on the canvas**
  with the anchor chip pre-filled; create → node badge appears without
  visiting the Tasks tab.
- Open a task → edit title, status (dropdown), priority, description, labels;
  add a subtask; every change round-trips.
- Two open tasks on one node → amber hot badge on canvas + sidebar.

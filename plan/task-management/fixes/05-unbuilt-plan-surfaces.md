# Fix 05 — Planned surfaces that were never built (T3/T4 remainder)

Inventory of what the plan settled but the implementation skipped, beyond
the detail panel ([fix 04](04-detail-panel-gaps.md)). Ordered by leverage.

## 1. Anchor API violates README decision 9 (do with fix 02)

Decision 9: *"Linking is idempotent and keyed by node … never a list
index."* The implementation shipped the opposite:

- `add_anchor` (`task_service.py:314-321`) **appends without checking** —
  double-click = duplicate anchor rows, double-counted summaries.
- `remove_anchor` / `re_anchor` are **index-keyed**
  (`task_service.py:323-356`, routes `/{index}`) — exactly the shape the
  plan forbids: two surfaces mutating the same task shift each other's
  indices; a retry after timeout deletes the wrong anchor.
- **`anchors/move` does not exist** — 03 defines it as the single endpoint
  behind drag-transfer, the Move… picker, *and* re-anchor (a move whose
  source is dead). The shipped `re-anchor/{index}` covers one of the three.

Fix while touching the routes for [02](02-task-routes-404.md): key
add/remove by `node_id` (add = no-op if present; remove = no-op if absent),
replace `re-anchor/{index}` with `POST /tasks/anchors/move`
(`from_node_id`, `to_node_id`, source may be dead, one system note).
Frontend `reAnchor(index)` becomes `moveAnchor(fromNodeId, toNodeId)`.

## 2. Scope pill — the board ignores where you're standing

Plan (README decision 8, 03, 04): board read takes `scope_node_id`,
resolved server-side over the subtree, with a per-tab
*This node · This tab · All* pill defaulting to *This tab*, exactly like
`historyScope`. Shipped: `get_board_payload` has no scope parameter, no
pill in `FilterBar`, no `taskScope` in the slice — the board is always
*All*. This is why the tab feels disconnected from the graph. The commits
view (`versioning/commits.py`) is the pattern to copy for the server-side
subtree resolution; the query key already has the right shape to grow one
more segment.

## 3. Node popover — the badge is a dead end

05: badge click opens the linking popover (task rows with link toggles ·
*Attach task…* search · *New task here* empty state · drag-transfer to
another node card). Shipped: the canvas badge exists, but clicking it just
selects the first anchored task (`EnhancedNode.tsx:219`) — with two tasks
on a hot node there is no way to see or choose the second, which guts the
convergence story. The context menu's `attach-task` action (06) is also
absent. Build the popover once; the context-menu action opens the same
component in attach mode.

## 4. Blockers sidebar section

05: collapsible section under the tree — hot nodes ranked by `open_count`,
click focuses the node, hidden when empty. Not built. The data is already
one `useAnchorSummary` read; the sidebar already has section machinery
(`useSidebarPanels`). Small build, closes T4's "amber everywhere" loop
(sidebar *badges* did ship — `TreeNode/NodeContent.tsx`).

## 5. Board polish that changes behavior (not just looks)

- **Column `+` settings popover** (04): rename/recolor/`is_done`/delete —
  `PATCH /tasks/board` and its guard rails exist server-side with no UI.
- **Search misses `description`** — 04 lists it in the predicate;
  `useTaskFilters` matches title/key/labels/qnames only.
- **Column counts when filtered** should gray to `3 of 7`, never hide
  silently (04) — verify against the shipped `BoardColumn`.
- **Drag start data**: `TaskCard`'s `onDragStart` never calls
  `e.dataTransfer.setData(...)` — Chrome tolerates it, Firefox won't start
  the drag at all. One line (`setData("text/plain", task.id)`), and it
  future-proofs the popover drag-transfer which must distinguish task-row
  drags from node drags.

## 6. Socket-driven cross-surface refresh (verify after fix 01)

`useSocketSync` invalidates `queryKeys.tasks.board(data.project_id)` with
the **backend's** project id. The frontend keys are built from
`toProjectApiId(...)` (`ProjectSchema/{slug}`). Confirm
`uow.project.id` arrives in exactly that shape — if it's ever the bare
slug, the invalidation prefix silently misses and canvas badges won't
live-update even once the caches are fixed. One `console.assert` in dev or
a normalization through `toProjectApiId` in the handler settles it.

## Explicitly still out of scope (unchanged from 06)

Multi-board, sprints (the List divide is the seam), assignees,
task↔commit auto-linking, cross-branch sync, LLM subtask suggestions —
all remain named seams, not gaps.

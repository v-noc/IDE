# v2 · 09 — Frontend Implementation Spec

Execute after [08](08-backend-spec.md) §1–§2 exist (routes + no-cache) —
nothing here can be verified against a backend that 404s. Visual truth
lives in 01–04; interaction truth in 07; this doc is the wiring order and
the tricky client logic. All paths under `src/frontend/src/`.

## §1 Foundation (do first, everything depends on it)

### §1.1 `features/Dashboard/features/Tasks/theme.ts`

Rewrite to the full token sheet in [01](01-design-tokens.md): export
`SURFACE`, `BORDER`, `TEXT`, `GREEN`, `AMBER`, `TYPES`, `PRIO`,
`KIND_ICON`, `COLUMN_DOTS` plus helper fns `typeChipStyle(type, small?)`,
`anchorChipStyle(state: 'resolved'|'hot'|'unresolved')`. Components import
from here only — grep for `#` hex and Tailwind semantic colors in the
Tasks folder afterwards; both should be ~zero.

### §1.2 `services/tasks/api.ts` — query-param ids (L7)

Every function that takes `taskId` moves it into the query string via the
existing `projectQs` helper:

```ts
// BEFORE  api(`${TASKS}/${taskId}/move${projectQs(pid)}`, …)
// AFTER   api(`${TASKS}/move${projectQs(pid, { task_id: taskId })}`, …)
```

Signature changes: `removeAnchor(pid, taskId, nodeId)` (node, not index) ·
new `moveAnchor(pid, taskId, fromNodeId, toNodeId)` → `POST
/tasks/anchors/move` · delete `reAnchor(index)` · board columns PATCH →
`/tasks/board-columns`. `URLSearchParams` already encodes the `/` in ids —
no manual encoding.

### §1.3 `useTasks.ts` — shared error surfacing

Add one helper and use it as `onError` in **every** mutation (after any
rollback):

```ts
function toastTaskError(err: unknown) {
  const detail = (err as ApiError)?.response?.detail;
  toast.error(typeof detail === "string" ? detail : "Task update failed");
}
```

The backend's refusal sentences (cycles, dead nodes, call rule) are
user-facing copy — show them verbatim (L6). Use the app's existing toast
util (check `sonner`/`toast` imports elsewhere in `features/Dashboard`).

### §1.4 Socket id normalization

In `useSocketSync.ts`, wrap the incoming id:
`queryKeys.tasks.board(toProjectApiId(data.project_id))` (same for
summary). Costs nothing, removes the silent-miss risk if the backend ever
emits a bare slug.

## §2 Mutation recipes (the tricky client logic — copy these shapes)

All keys come from the existing `useTaskQueryKey(projectId)` (board) and
the summary key builder — never hand-build keys.

### §2.1 Optimistic move (board drag, list drag, subtask checkbox)

Already correct in `useMoveTask` — keep the shape:
`onMutate` cancel → snapshot → patch `status`+`rank` → return snapshot;
`onError` restore snapshot **then** `toastTaskError`; `onSettled`
invalidate board + summary. The subtask checkbox reuses this same hook
(child task id, target = first `is_done` column or first workflow column —
resolve from `board.columns`, never hardcode `"done"`).

### §2.2 Optimistic anchor toggle (add/remove)

Anchors change hot-state everywhere, so patch board cache optimistically
but **always** invalidate summary on settle:

```ts
onMutate: patch the task's anchors array in the board cache
          (add: {node_id, qname: pickerQname, kind, is_resolved:true} placeholder;
           remove: filter by node_id)
onError:  rollback + toastTaskError
onSettled: invalidate board AND anchor-summary
```

Caveat the implementer must respect: after `add`, the server may return a
**different node_id than sent** (call → target resolution, L3). The
optimistic placeholder is cosmetic; the settle-invalidate brings the
truth. Never key UI state on the sent id — key on the refetched anchors.

### §2.3 `useMoveAnchor` (transfer / re-anchor)

No optimistic patch (two ids + merge semantics = too many branches to
fake): plain mutation, spinner on the row, invalidate board + summary on
settle, `toastTaskError` on error. The Re-anchor picker calls this with
`from = the dead anchor's node_id`.

### §2.4 Subtask link/create/unlink

`useAddSubtask` exists — extend payload per 08 §1 (`child_id` XOR inline
`{title}`). Add `useRemoveSubtask(parentId, childId)`. Both: no optimistic
patch, invalidate board on settle (summary too — subtasks feed closure
counts). Cycle refusal arrives as 409 → toast shows the sentence; the
inline input must **not** clear on error ([07](07-subtasks-and-node-selection.md) §A).

## §3 Board restyle (per [02](02-board.md))

1. `columnUtils.ts`: delete `workflowColumns`/`backlogColumn` filtering —
   `BoardView` maps **all** `board.columns` in order. Remove the
   backlog-link button and `listScrollToBacklog` wiring.
2. `BoardView` / `BoardColumn` / `TaskCard`: apply 02's metrics exactly
   (column 252px/radius 11, drag-over green pair, card paddings, priority
   bar geometry, chips). Card anchor chips: all anchors, not just
   `anchors[0]` (mock renders the full set) — chip click
   `stopPropagation()` then navigate-to-node.
3. `useBoardDnd.ts`: add `e.dataTransfer.setData("text/plain", taskId)`
   in `handleDragStart` (Firefox). Keep rank math.
4. `FilterBar`: per 02 — segmented control, **anchored-node mono filter**
   (replaces the general search; predicate in `useTaskFilters` becomes
   `task.anchors.some(a => a.qname.toLowerCase().includes(q))`, empty q
   matches all), summary `n open · n hot node`, green `+ New task`.
   Remove the Board/List view switcher (List is out of v2 — leave the
   `list/` files untouched but unreferenced).

## §4 Detail panel rebuild (per [03](03-detail-panel.md), section order fixed)

Rebuild `TaskDetailPanel.tsx` top-to-bottom in 03's order — nine sections,
each independently committable:

1. Header (+ nav-stack ← already exists — keep).
2. Title input: hover/focus borders per 03 §1; commit on blur+Enter, Esc
   reverts, empty reverts. Use `defaultValue` + local dirty ref, not
   controlled-on-every-keystroke (avoids caret jumps on refetch).
3. Fields grid 2×2 (read-only; STATUS dot from `board.columns` color).
4. Labels row (render-only).
5. Description: read box ↔ textarea swap, PATCH on blur; placeholder
   state when empty.
6. Anchored nodes: bordered list, per-row actions
   (`Show on canvas` / `Re-anchor` → picker → `useMoveAnchor`), hover-✕
   unlink → `useRemoveAnchor`, `+ Add anchor` row → node picker (§5.3),
   `⚓ Anchor current node` chip when the tab's active node isn't
   anchored. Empty state: one placeholder row, never a bare heading.
7. Subtasks: checkbox (§2.1), title-click nav-push, shared chip, status,
   hover-✕ unlink, `+ Add subtask` inline search-or-create
   ([07](07-subtasks-and-node-selection.md) §A), `✦ Suggest` flow.
8. Dependencies: rows from `blocked_by` + `blocks` (enriched by 08 §6).
9. Activity + note input. **Delete the `Focus on canvas` button.**

Panel width/colors per 03 shell. Every mutation = the §2 hooks; the panel
never calls `tasksApi` directly.

## §5 Create flow (per [07](07-subtasks-and-node-selection.md) §B, `../fixes/03`)

1. **Move `<NewTaskModal projectId=…/>` to `pages/Dashboard.tsx`** (next
   to `SidebarDialogs`); delete it from `Tasks/index.tsx`. Clear
   `newTaskPreset`+`newTaskModalOpen` on project/branch change (subscribe
   in the slice or clear in Dashboard's project-switch effect).
2. Board `+ New task` and column `+`: preset gains the tab's active node
   (`activeNodeId[tabId]` → resolve node via the existing
   `findNodeByIdWithDescendantCache`) as `anchorNodeId/Qname/Kind`.
3. **Client call pre-resolution**: when the preset node is a call
   (`node_type === 'call'`), use `node.target` (`types/project.ts`) for
   the chip; if `target` is missing, show the chip amber with
   `resolves on create` — the server settles it (L3).
4. Node picker component (`components/NodePickerDialog.tsx`): clone the
   `SelectNodeDialog` pattern; list functions/classes/files/folders only;
   rows per 07 §B. Used by modal `+ add`, panel `+ Add anchor`, and the
   Re-anchor flow (pre-seeded query = dead anchor's qname tail).

## §6 Canvas & sidebar (per [04](04-canvas-and-sidebar.md))

1. Badge pill + hot glow + focused ring styles into
   `getNodeStyle.ts`/`EnhancedNode` from theme tokens; `hotGlow`
   keyframes live in `index.css` gated by
   `@media (prefers-reduced-motion: no-preference)`.
2. New `components/NodeTaskPopover.tsx` (read-only, 04 spec): opens from
   badge click (`popoverNodeId` in tasksSlice — add it; badge button gets
   `nodrag nopan` classes), rows from board cache filtered by
   `anchorSummary.nodes[nodeId].open_task_ids`, row click →
   `setSelectedTaskId` + close; overlay + Esc close.
3. Sidebar chips + Tasks-tab count chip restyle (tokens only, logic
   exists).
4. Remove the lens entry (`lensTaskId` stays in the slice, unused for
   now).

## §7 Definition of done (run these by hand)

1. Create from board → appears without refresh; create from canvas
   right-click on a **call** → chip shows the target function; created
   task is anchored to it.
2. Drag `To do → In review` → survives a hard refresh; activity shows
   "Moved to In review".
3. Anchor the same node twice from two surfaces → one row; unlink an
   unresolved anchor → works.
4. Re-anchor a dead anchor via the picker → row flips to resolved; when
   the picked target was already anchored → row disappears + "merged"
   note in activity.
5. Add-subtask: search-link an existing task from another parent → shared
   chip on both; attempt a cycle → sentence toast, input keeps text.
6. Two open tasks on one node → amber badge + glow + sidebar chip +
   popover lists both; check one done → all three surfaces drop to green
   without refresh.
7. Screenshot the detail panel next to the mock at 384px — a reviewer
   finds no unlisted difference.

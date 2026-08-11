# Fix 03 — Tasks are always created without anchors; "New task here" is dead

An anchor-less task defeats the whole plan: no anchors → no hot nodes → no
convergence signal (the README's "killer feature"). Three independent causes,
all three needed the fix.

## Cause 1 — the modal only exists inside the Tasks tab

`NewTaskModal` is mounted solely inside `TasksBoard`
(`features/Tasks/index.tsx:134`), which lives under
`<TabsContent value="tasks">` (`WorkspaceTabs.tsx:114-123`). Radix
**unmounts inactive tab content** — so while the user is on Canvas, Code, or
Docs, the modal component does not exist.

The canvas context-menu action works only up to the store:
right-click → *New task here* → `openNewTaskModal({anchorNodeId…})`
(`useNodeHandlers.ts:135-144`) sets `newTaskModalOpen = true` … and nothing
renders. Worse: the flag and preset **persist**, so the modal pops up
unexpectedly when the user later opens the Tasks tab — with a stale anchor
preset they no longer remember. This is the "kind of a mess" behavior.

**Fix:** mount `<NewTaskModal projectId={…}/>` once at the Dashboard level
(next to `SidebarDialogs` in `pages/Dashboard.tsx` — it's a portaled Dialog,
placement is free) and remove it from `TasksBoard`. One instance, always
mounted, opens from any surface. Clear `newTaskPreset` on project/branch
switch so a stale preset can't leak across contexts.

## Cause 2 — board `+ New task` never pre-fills the active node

The filter-bar button passes only a column
(`features/Tasks/index.tsx:89-91`), so every board-side create starts
anchor-less. Plan 04 ("Creating a task while scoped pre-fills its anchor
from the scope node") and 06 ("the same pre-fill applies when the modal
opens from the board while the tab has an active node") both specify the
pre-fill.

**Fix:** in `TasksBoard`, read the tab's active node
(`activeNodeId[tabId]`, falling back to the tab root — same source the
commits scope uses) and pass
`{ columnId, anchorNodeId, anchorQname, anchorKind }` to
`openNewTaskModal`. Pre-filled means removable — the modal's existing
"Remove" chip already covers that.

## Cause 3 — an anchor-less task can never gain an anchor

Once created bare, there is no surface anywhere to attach a node:

- The modal has no node picker (06 specifies `+ add` via the
  `SelectNodeDialog` machinery).
- The detail panel has neither the `⚓ Anchor current node` chip nor
  `+ Add anchor` (05's Anchored-nodes spec) — the screenshot's empty
  "ANCHORED NODES" header with nothing under it is this gap.
- The node popover with its *Attach task…* row (05) doesn't exist at all
  ([fix 05](05-unbuilt-plan-surfaces.md)).

**Fix (minimum to close the loop):** add `+ Add anchor` to the detail
panel's Anchored-nodes section opening a `SelectNodeDialog`-style picker →
`tasksApi.addAnchor` (endpoint exists; works once
[fix 02](02-task-routes-404.md) lands). Then the Anchor-current-node chip:
when the workspace tab has an active node not already anchored, render the
one-click chip exactly as 05 describes.

## Verify

- On the **canvas**, right-click `dd` → *New task here* → modal opens
  immediately, anchor chip pre-filled `ƒ main.dd`; create; the node badge
  shows `1` without visiting the Tasks tab.
- On the **board** with an active node in the tab, `+ New task` → anchor
  pre-filled; remove chip → creates bare, as chosen.
- Open a bare task → `+ Add anchor` → pick a node → the anchor row appears
  and the node badge updates.
- Switch projects with the modal preset set → no ghost modal on the next
  Tasks-tab visit.

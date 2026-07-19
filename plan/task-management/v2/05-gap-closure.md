# v2 · 05 — Gap Closure: shipped code → v2, data audit, build order

## Data availability — everything the mock shows is already served

`TaskService._enrich_task` puts on the wire: `title`, `description`,
`labels`, `task_type`, `status`, `priority`, `created_at`, `updated_at`,
`anchors[].{qname,kind,is_resolved}`, `subtasks[].{id,key,title,status,shared}`,
`subtask_progress`, `blocked_by[]` (enriched), `blocks[]` (bare ids),
`blocked`, `notes[].{text,at,origin}`. The anchor-summary endpoint serves
per-node `{open_count, hot, open_task_ids}`.

**Conclusion: v2 needs zero new endpoints.** Two small backend touches
only:

1. Enrich `blocks` like `blocked_by` (id/key/title/status) — or resolve
   client-side from the board payload as 03 allows.
2. The write paths must actually work: land `../fixes/02` (per-task routes
   404 on `TaskSchema/…` ids) and `../fixes/01` (Cache-Control staleness)
   first — no UI fidelity survives a board that won't refresh.

## Component-by-component change list

| Shipped file (`features/Dashboard/features/Tasks/`) | v2 action |
|---|---|
| `theme.ts` (19 lines, partial) | **Rewrite** to the full token sheet in [01](01-design-tokens.md); export type/priority/kind/column maps so no component holds hex |
| `components/detail/TaskDetailPanel.tsx` | **Rebuild against [03](03-detail-panel.md)** — the biggest gap. Add: title hover/focus treatment, 2×2 fields grid (STATUS dot, PRIORITY color, CREATED, UPDATED), labels row, DESCRIPTION box + click-to-edit, anchor rows in the bordered-list style with per-kind icon colors and the Re-anchor/Show-on-canvas button styles, subtask checkboxes + strike-through + status column + the two dashed buttons, DEPENDENCIES section, activity dot-feed. Remove `Focus on canvas`. Keep nav stack |
| `components/TaskCard.tsx` | Restyle to [02](02-board.md): exact card paddings/colors, priority-bar geometry (5/8/11px), progress `✓ n/n` with the svg check, blocked pill, anchor chips with the three states + tooltips + brightness hover |
| `components/board/BoardView.tsx` + `columnUtils` | **Render all 5 columns** — delete the `workflowColumns`/backlog-link split; column shell + drag-over treatment per 02 |
| `components/BoardColumn.tsx` | Header per 02 (dot size, count mono, `+` hover), drop-target colors |
| `components/FilterBar.tsx` | Restyle segmented control to mock; **replace the general search with the 220px mono anchored-node filter** (predicate over anchor qnames); summary string `n open · n hot node`; green `+ New task` exact colors. Drop `/`-to-focus or keep it wired to the new input (keep — invisible, harmless) |
| `components/list/*` (ListView, TaskRow, InlineAddRow) | **Out of v2.** Leave the files; remove the view switcher from the bar (mock has none). Revisit if the backlog column proves unwieldy |
| `hooks/useTaskFilters.ts` | Swap `query` matching to the anchored-qname predicate; keep type filter |
| `hooks/useBoardDnd.ts` | Add `dataTransfer.setData` on drag start; keep rank math |
| `components/NewTaskModal.tsx` | Mount at Dashboard level + anchor pre-fill per `../fixes/03`; restyle inputs/buttons to 01 tokens |
| `EnhancedNode.tsx` / `NodeHeader` | Badge pill + hot glow + focused ring per [04](04-canvas-and-sidebar.md); badge click opens the **popover** (new component) instead of selecting the first task |
| `Sidebar/TreeNode/NodeContent.tsx` | Restyle count chips to the green/amber pill tokens |
| `WorkspaceTabs.tsx` | Tasks count as a styled chip per 04 |
| store `tasksSlice` | Add `popoverNodeId: string \| null`; retire `lensTaskId` usage from the panel (lens returns post-v2) |

## Build order (each step demoable)

1. **Fixes 02 + 01** (routes + cache) — mutations and refetches work.
2. **Tokens** (`theme.ts`) + **TaskCard/Board/FilterBar** restyle — the
   board screen matches the mock side-by-side, 5 columns, drag works.
3. **Detail panel rebuild** (03) — open VN-9-shaped task: every section
   present, title/description/notes editable, subtask checkboxes
   round-trip.
4. **Canvas + sidebar** (04) — badge, glow, popover, chips.
5. **Modal mount + anchor pre-fill** (`../fixes/03`) — anchored creation
   from canvas works end-to-end; hot nodes reachable by a user for the
   first time.

## Acceptance — the five reported complaints, closed

| Complaint | Closed by |
|---|---|
| "Where is the update / title / description / node — doesn't exist" | Step 3 (03: sections 1, 2, 4, 5) |
| "UI is not the same as the design" | Steps 2–4 (01 tokens everywhere; side-by-side check per v2 README) |
| "After creating I have to refresh" | Step 1 (`../fixes/01`) |
| "Move to next column does not update" | Step 1 (`../fixes/02`) + 02's DnD contract |
| "Always creates a task, no anchor node" | Step 5 (`../fixes/03`) |

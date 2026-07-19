# 05 — Detail Panel & Canvas Integration

Every surface here mounts into a slot that already exists: the right-sidebar
slot, the node header, the context menu, the sidebar tree. The canvas work is
badges, glow, popover, and the lens — the graph rendering itself is untouched.

## Right-slot arbitration

`Dashboard/components/Layout.tsx` exposes one `rightSidebar` slot; the Agent
panel lives there today. The rule (README decision 6): **the slot is
exclusive**.

- `selectedTaskId != null` (tasksSlice) → the slot renders `TaskDetailPanel`.
- Closing it (✕, Esc, selecting nothing) → the previous occupant returns; the
  Agent panel keeps its own state (its store survives unmount — verify the
  panel's stream/mirror stores are module-scoped, not component-scoped, which
  they are in the Agent feature's store/ folder).
- Selecting a task while the agent is mid-run does NOT cancel the run; the
  panel is hidden, not killed. A thin "agent running" pill in the detail
  panel header links back.

## TaskDetailPanel (`features/Tasks/components/detail/`)

384px, mock layout, top to bottom. Every mutation goes through the same
`useTasks` mutations as the board (04) — the panel is a view, not a second
data path.

| Section | Behavior |
|---|---|
| Header | type badge · `VN-12` mono key · ✕. |
| Title | borderless input, green focus ring; PATCH on blur/Enter. |
| Fields grid | STATUS (column dot + name, dropdown of columns → `move`) · PRIORITY (dropdown) · CREATED / UPDATED (read-only). |
| Labels | chips + inline add/remove → PATCH. |
| Description | markdown; render read view, click-to-edit textarea, PATCH on blur. Reuse the docs editor's markdown renderer if trivially importable; else a minimal renderer — do not grow a second editor stack for v1. |
| **Anchored nodes** | Top of the section, when the workspace tab has an active node not already anchored: an **`⚓ Anchor current node — ƒ main.dd`** one-click chip (idempotent add; the chip flips to "anchored ✓" and becomes the detach toggle). Rows: kind icon · qname · state chips · actions. Resolved → `Show on canvas` (tab→canvas, focus + auto-expand) · `Move…` (node picker → `anchors/move`) · unlink (idempotent remove). Hot → `hot · 2 tasks` amber chip (anchor-summary data). Unresolved → amber-tinted row, `⚠ unresolved`, `Re-anchor` button → candidate picker dialog (`GET /tasks/re-anchor-candidates`, seeded with snapshot qname; picking calls the same `anchors/move`). `+ Add anchor` at the bottom → node search (reuse `SelectNodeDialog` patterns). |
| **Subtasks** | `SUBTASKS · 2/5` (closure-deduped from API). Rows: checkbox (toggles child between its column and the first `is_done` column — the mock's toggle semantic, made explicit) · title (click → `selectedTaskId = child`, panel navigates in place) · `⑂ shared` purple chip when `shared` · status. Buttons: `+ Add subtask` (inline title input → create-and-link) · `✦ Suggest from dependencies` (06). |
| **Dependencies** | `blocked by` (red label) / `blocks` (amber label) rows from derived fields; click navigates; add via task search popover → `blocked-by` endpoints. |
| **Activity** | notes list (system + user, mono timestamps) + `Add a note…` input → notes endpoint. |

Panel navigation (subtask/dependency clicks) pushes onto a small local stack
so ✕ is always "close panel" and ← is "back to parent task" — without this,
DAG hopping strands the user.

## Canvas node badge + hot treatment

`NodeHeader.tsx` already renders conditional chips (status dot, diff badge) —
the task badge is one more, driven by the anchor-summary query keyed by
`node.id`:

- **1 open task** → green-tinted count chip `1` after the node name.
- **hot (≥2)** → amber chip + amber border + the soft `hotGlow` pulse on the
  whole card (mock's keyframes; respects `prefers-reduced-motion` by falling
  back to the static amber border). Border/glow applied in `EnhancedNode`'s
  style computation next to the existing status/diff styling — hot is loud,
  but it is *one* amber system: chip, border, sidebar badge, blockers rows all
  read from the same `Tasks/theme.ts` tokens (04).
- Zero tasks → nothing rendered; the graph stays quiet by default.

Badge click opens the **popover** (anchored to the chip, shadcn popover):
`OPEN TASKS · dd` header with `● hot node` suffix when hot. The popover is
the node's **linking surface**, not just a list:

- **One row per anchored task** (type badge · title · status, mock layout);
  row click sets `selectedTaskId`. Each row carries a **link toggle** —
  unchecking detaches the task from this node (idempotent remove, optimistic
  flip, badge count follows immediately).
- **`＋ Attach task…`** row at the bottom: inline search over open tasks
  (title + `VN-n` key, board query cache — no fetch); picking one anchors it
  to this node (idempotent add). The same row offers *"New task here…"* as
  its empty-state action, jumping to the modal (06).
- **Drag-transfer**: a popover row is draggable; dropping it onto another
  node card calls `anchors/move(this_node → target_node)` — the anchor
  travels, both badges update, the task's activity records it. Node cards
  register as drop targets only while a task-row drag is live (same
  `nodrag`/`nopan` care the header buttons already take with React Flow).
  The `Move…` picker in the detail panel is the no-drag fallback for the
  same operation.
- A node with **zero tasks** still opens a minimal popover from the context
  menu's *Attach task* action (see below) — attach search + "New task here"
  — so linking never requires visiting the board.

Outside click closes. The popover reads everything from the board and
anchor-summary query caches.

`NodeContextMenu` gains **`Attach task`** next to *New task here* (06): same
popover, opened for nodes that have no badge yet — link-to-node and
link-off-node are both one gesture from the canvas.

## Task lens

State: `lensTaskId` in tasksSlice. Entered from the detail panel ("Focus on
canvas") or a card's overflow menu; implies switching to the Canvas tab.

- Member set = the task's anchored node ids ∪ anchored node ids of its subtask
  closure (resolved anchors only).
- **Dimming via React Flow's own mechanisms**: non-member nodes get a
  `lens-dimmed` class (opacity ~.15, `pointer-events` preserved), member
  nodes get a colored ring (green ring family, per mock's focused style);
  edges dim unless both endpoints are members. This is a pure
  className/style pass in the existing node/edge mapping — no second
  renderer, no layout change.
- Floating bar, top-center of the canvas: green pulse dot · task title ·
  `n nodes` · `Exit lens`. Esc exits. Entering the lens for a task with zero
  resolved anchors is refused with a toast naming why.
- Lens state is per-workspace-tab (keyed like the rest of uiSlice state) and
  cleared on branch/project switch.

## Sidebar tree + Blockers

- **Badges**: `TreeNode/NodeRow` renders the count chip right-aligned (mock:
  `dd 3` amber, `runner 1` green) from the anchor-summary map — exact-node
  counts in v1 (02). Zero = no chip; the tree stays clean.
- **Blockers section**: collapsible section under the tree (the sidebar
  already has panel sections via `useSidebarPanels`): hot nodes ranked by
  `open_count` desc — row = kind icon · qname · amber count; click = focus
  node on canvas. Empty state: section hidden entirely (a permanently empty
  "Blockers" header would train users to ignore it).

## What is deliberately not built

- No task counts on Docs/Code tabs, no per-document anchoring — nodes only.
- No presence/assignee/avatar anywhere: V-NOC is single-user today; the mock
  agrees.
- No board-side mini canvas or graph preview in the detail panel; "Show on
  canvas" navigating the real canvas is the feature.

# Fix 04 — Detail panel shipped as a skeleton

The design (mock + plan 05) vs `TaskDetailPanel.tsx` (303 lines). Nothing
here was un-planned — 05's section table specifies each row below. The
backend already serves or accepts almost all of it; most of this is pure
frontend build, **gated on [fix 02](02-task-routes-404.md)** (the endpoints
currently 404).

## Section-by-section audit

| 05 spec | Shipped | Gap → what to build |
|---|---|---|
| Header: type badge · key · ✕ (+ ← after DAG navigation) | ✅ | — |
| Title: borderless input, PATCH on blur/Enter | ⚠️ blur only | Add Enter-to-commit; show a failure toast (02) |
| **STATUS: dropdown of columns → `move`** | ❌ read-only text | Dropdown listing all columns **including Backlog** (04: the panel is the one place a board task can be parked); on select call the existing `useMoveTask` with a top-of-column rank |
| **PRIORITY: dropdown** | ❌ read-only bars | Dropdown → `updateTask({priority})`; backend appends the system note already (`task_service.py:183-191`) |
| CREATED / UPDATED read-only fields | ❌ | Render `created_at`/`updated_at` (already on the wire, `_enrich_task`) |
| **Labels: chips + inline add/remove** | ❌ (cards render labels; panel ignores them) | Chips + inline input → `updateTask({labels})` |
| **Description: markdown, click-to-edit** | ❌ entirely absent | Read view + click-to-edit textarea, PATCH on blur; reuse the docs markdown renderer if trivially importable, else minimal renderer (05's "no second editor stack" rule) |
| Anchored nodes: rows with kind icon · qname · state chips | ⚠️ rows + hot chip + Show-on-canvas + Re-anchor exist | Missing: **unlink** (idempotent remove), **Move…** picker, **`+ Add anchor`**, **`⚓ Anchor current node` chip** (see [fix 03](03-anchorless-create-and-new-task-here.md)); empty state currently renders a bare header — show the add-affordances instead |
| **Subtasks: checkbox (child ↔ first `is_done` column) · title-click navigation · `⑂ shared` · status text** | ⚠️ title-click + shared chip only | Add the checkbox (calls `move` on the child — 05 makes the mock's toggle semantic explicit), per-row status, done strike-through; **section renders even when empty** (it's hidden behind `subtasks.length > 0` today — the mock always shows it) |
| **`+ Add subtask` inline create · `✦ Suggest from dependencies`** | ❌ | Inline title input → `useAddSubtask` (endpoint + hook already exist, unused); suggest button reuses `useSuggestDependencies` seeded from the first resolved anchor (06) |
| **Dependencies: blocked by / blocks rows, click-navigate, add via search** | ❌ | `blocked_by` objects are already on the wire; `blocks` arrives as bare ids — either enrich server-side like `blocked_by` or resolve client-side from the board payload. Add via task-search popover → `addBlockedBy` |
| Activity: system + user notes + input | ⚠️ | Renders only when notes exist; input works. Always render the section; timestamps mono per mock |
| Panel nav stack (← back after subtask hop) | ✅ | — |

## The lens trap (ship-blocker inside this panel)

"Focus on canvas" sets `lensTaskId` (`TaskDetailPanel.tsx:225`) and
`EnhancedNode` dims non-members — but **the lens bar was never built**: no
floating `task title · n nodes · Exit lens` bar, no Esc handler
(plan 05 "Task lens"). Entering the lens today leaves the canvas dimmed
with no way out short of knowing the store. Either ship the bar + Esc with
this fix, or disable the button until the bar exists. Also enforce 05's
guard: refuse the lens with a toast when the task has zero resolved anchors.

## Not bugs (deliberate per 05 — don't "fix")

- No assignees/avatars, no mini-canvas preview in the panel, no per-document
  anchoring. The panel navigating the real canvas is the feature.

## Verify

Round-trip every field on one task: status via dropdown (lands on the board
column), priority, labels, description; check a subtask checkbox and watch
`SUBTASKS · n/m` and the parent card's progress update; add a blocked-by and
see the `⊘ blocked` pill appear on the dependent card; enter and exit the
lens with Esc.

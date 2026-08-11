# 06 — Graph & Agent Integration

The two directions of integration: the graph feeding task creation
(deterministic, v1), and the agent creating tasks (two-gate tool, later). Plus
the ledger of what stays out.

## "New task here" (canvas → task)

`Dashboard/components/NodeContextMenu.tsx` gains two actions in the existing
`onAction` union, rendered after *Prompt builder*:

- **`"new-task"`** → opens `NewTaskModal` (04).
- **`"attach-task"`** → opens the node's task popover in attach mode (05) —
  link an *existing* task to this node in two clicks, no board visit.

`NewTaskModal` opens with:

- **Anchor pre-filled** from the node the menu opened on — removable chip,
  `+ add` opens node search (reuse `SelectNodeDialog` machinery). The same
  pre-fill applies when the modal opens from the **board** while the tab has
  an active node or a node/tab scope (04): creating a task while "standing
  on" a node anchors it there by default. Pre-filled means removable — one
  click detaches before create.
- Title (autofocused), type, priority, description — one screen, no wizard.
- **Suggested subtasks** section (below the anchor): the node's direct
  dependencies, each row `checkbox · kind icon · qname`. Checked rows are
  submitted with the create call (`POST /tasks/` then
  `POST /tasks/{id}/subtasks` inline-create per suggestion, or the one-shot
  `subtask_of`-style payload — one round trip preferred), each new subtask
  titled after the dependency (`Refactor dd()` pattern: user edits later) and
  **anchored to that dependency**.

### Where suggestions come from (deterministic law)

Dependencies = graph facts already stored, no LLM:

1. **Callees**: the node's `call_children` (and call-group members) resolved
   through `CallSchema.target_function` / `target_class` → the target
   function/class nodes.
2. **Children**: for file/class nodes, direct `function_children` /
   `class_children`.

Served by a small `TaskService.suggest_dependencies(node_id)` reading the
existing repos (the same traversals the walkthrough context builder does) —
deduped, capped (~12), one line each. If the node has no dependencies the
section simply doesn't render. The same endpoint powers the detail panel's
`✦ Suggest from dependencies` button (05), seeded from the task's first
resolved anchor.

## Task context for the agent (cheap, high-leverage)

When a user attaches a node to the agent composer, the context factory
(agent-v2 `context-engineering/02`) already assembles parent/children/docs.
Add one optional block, fed by the anchor summary + board cache:

```xml
<open_tasks node="main.dd">
  VN-12 Fix logging bug (bug, in progress) — also anchored: —
  VN-15 Speed up runner (improvement, todo, blocked by VN-12)
</open_tasks>
```

One block, capped, open tasks only. The agent can now answer "what's pending
on this function?" truthfully with zero new tools. This is the first
integration to ship after T4 because it is pure read.

## `plan_tasks` — the future agent tool (specced, not built)

When task creation goes agentic, it follows the grouper's two-gate shape
exactly (`plan/grouper/03-review-gate.md`):

- **Registry**: `plan_tasks` entry in `Agent/tools/registry.ts`
  (coming-soon gated, like describe/document/group today) + a backend
  `ToolSpec` in `app/agent/tools/`.
- **Gate 1 — estimate**: attached node + user intent → knobs (max tasks, max
  depth of subtask nesting) + honest LLM-call count.
- **Run (read-only)**: model reads the node's context (context factory) and
  proposes a task tree: titles, types, anchors chosen **only from node ids
  present in its context** (the agent-v2 law: no fabricated ids by
  construction), suggested subtask edges.
- **Gate 2 — review**: the proposal renders as an editable checklist (the
  grouper's ReviewView pattern); nothing exists until approve. Approve →
  `TaskService` writes everything in one commit batch (undo = revert batch,
  agent-v3 `shared/03` semantics). Cancel → zero writes.
- The DAG validator and anchor existence checks are the same service code the
  human path uses — the agent gets no private write path.

## Reparse & liveness (recap of the seams)

- v1: derived resolution + TTL-cached summary means the UI self-corrects
  without parser involvement (02).
- Seam 1: `tasks.summary_changed` socket emit at the end of a parse commit
  batch — belongs to the watcher/scheduler work in
  `plan/parser-orchestrator-refactor/phase-6`, not here.
- Seam 2: rename-detection proposing re-anchors (same-name node appearing in
  the same file as a vanished anchor target) — a *proposal* surfaced in the
  detail panel, never an auto-fix.

## Out of scope (named so they stay out)

| Not building | Why |
|---|---|
| Multi-board, swimlanes | One board per project until the single board hurts (README decision 4). |
| Sprints/iterations | **Named seam, shape sketched**: `SprintSchema` (name, start/end, state: planned/active/closed) + optional `sprint` ref on tasks. The List view's Active/Backlog divide (04) is built to receive it — Active becomes one table per sprint (active sprint first), Backlog stays the bottom section, and the kanban scopes to the active sprint. Nothing in the v1 schema or views changes shape; sprints only add a grouping level. Not v1: ship the divide, learn how it's used, then decide. |
| Assignees, watchers, notifications | Single-user IDE; no identity model exists to hang them on. |
| Task ↔ commit auto-linking ("this commit closes VN-12") | Real feature, but it belongs to the versioning surface; tasks already ride commits (03). |
| Cross-branch task sync | Seam named in 01; wait for real pain. |
| LLM-suggested subtasks in the modal | The modal stays deterministic; agentic planning is `plan_tasks` with gates. |
| Time tracking, estimates-in-points | Not the product. The only "estimate" in V-NOC is LLM spend. |

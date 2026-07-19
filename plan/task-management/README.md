# Task Management — Graph-Anchored Tasks (Board · Anchors · Hot Nodes)

Jira gives you tasks *about* code that live nowhere near the code. V-NOC's graph
makes a stronger contract possible: a task is **anchored to the nodes it is
about** — functions, classes, files, folders, calls. The board is a normal
kanban; the graph is where it pays off. When two open tasks converge on the
same node, that node is **hot** — the canvas says so before the merge conflict
does. That convergence signal is the killer feature; everything else in this
plan exists to make it truthful.

Designed against the approved mock (`V-NOC Tasks.dc.html` — board, task card,
detail panel, node badge, popover, sidebar badges) and the shipped codebase on
`agent_harness`. This plan is the buildable version of that mock: same visuals,
plus the data model, anchor lifecycle, and API the mock hand-waves.

## The user flow (the whole feature in one story)

1. The user right-clicks `dd` on the canvas → **New task here**. The modal
   opens with the anchor pre-filled (`ƒ main.dd`), plus a *Suggested subtasks*
   list built from the node's real callees — checked ones become subtasks
   anchored to those dependencies. No LLM involved; the graph already knows.
2. The task lands on the **Tasks** tab (new tab after Canvas), which has
   **two views over one payload**. **Board** is the execution kanban —
   `To do | In progress | In review | Done`, drag-and-drop, and **no backlog
   column**: parked work doesn't get a lane on the execution surface.
   **List** is the planning table, GitHub-Projects style: an **Active**
   section on top (status-grouped rows), **Backlog** at the bottom, and
   dragging a row across the divide is how work enters or leaves the board.
   A search box (`/` to focus) matches titles, `VN-n` keys, labels, and
   anchor qnames across both views. The tab opens **scoped, exactly like the
   commit history**: *This tab* by default (only tasks anchored under the
   tab's node), one pill flips to *This node* (the active node only) or
   *All* — remembered per tab.
3. **Linking is a toggle, not a ceremony.** The node popover lists open tasks
   with a link toggle — check to anchor the task to this node, uncheck to
   detach — plus an *Attach task…* search row over every open task. On the
   task side, when a node is active in the workspace, the detail panel offers
   a one-click **Anchor current node** chip.
4. `Refactor dd()` is added under the epic *Refactor main module* **and**
   under *Fix logging bug*. Subtasks form a **DAG, not a tree** — the row
   shows a `⑂ shared` chip instead of pretending the second parent doesn't
   exist.
5. Now two open tasks anchor to `main.dd`. The server's anchor summary flips
   the node **hot**: amber count chip + amber glow on the canvas card, amber
   badge in the sidebar tree, `1 hot node` in the board header, and `main.dd`
   tops the sidebar **Blockers** list.
6. Clicking the chip opens a popover listing the converging tasks; clicking a
   task opens the **detail panel** in the right-sidebar slot: anchors (with
   *Show on canvas* / *Move* / *Re-anchor*), subtasks with checkboxes,
   blocked-by / blocks, activity. Dragging a task row **out of the popover
   onto another node card moves the anchor there** — transfer is one gesture,
   recorded in the task's activity.
7. **Task lens**: from the detail panel the user focuses the task — the canvas
   dims except the task's anchored nodes, a floating bar names the task,
   *Exit lens* restores.
8. A refactor renames `load_config`. The reparse deletes the old node; the
   anchor keeps its last-known qname and shows **⚠ unresolved** with a
   *Re-anchor* action that suggests candidates by name — re-anchor is just a
   move whose source node is dead. The task never silently loses its meaning.

## Your idea → the shipped shape (what this plan changes and why)

| The raw idea (mock / prompt) | The plan's version | Why |
|---|---|---|
| `is_resolved: boolean` stored on the anchor | **Derived at read time** — the anchor stores `node_id` + a `qname`/`kind` snapshot; "resolved" = the node still exists | A stored flag goes stale the moment the watcher reparses. Deriving from the graph is always truthful and needs zero parser hooks in v1. The snapshot is what you show when the node is gone (02). |
| Hot = "2+ open tasks anchor the same node" | Same rule, but **computed server-side in one anchor-summary endpoint**, counting through the subtask closure with DAG dedupe | Four surfaces need the number (canvas, sidebar, board header, blockers list). One query, one cache, one invalidation — clients never re-derive closure logic and disagree (02, 03). |
| `status: string` column id; Done inferred by id | Columns carry an **`is_done` flag** | "Open task", progress `2/5`, and "blocked until blocker is done" all need done-ness. Inferring it from `id == "done"` breaks the first time a user renames a column (01). |
| `subtask_ids` DAG, "a subtask can have multiple parents" | Same, plus a **cycle validator on every edge add** and a shared-parent count the UI reads | A DAG without a cycle check becomes a graph with an infinite progress bar. The validator refuses with a sentence naming the cycle (01). |
| `rank: string` for drag ordering | **LexoRank-style key**, scoped to (board, column) | Midpoint string keys make a move one field update, no renumbering the column (01). |
| Detail panel "same slot as Agent panel, or a drawer next to it" | **Same right-sidebar slot, exclusive** — opening a task swaps the Agent panel out; closing restores it | 384px of drawer next to 420px of agent panel leaves no canvas. The slot already exists (`Dashboard/components/Layout.tsx` `rightSidebar`); exclusivity is one store field (05). |
| "Suggested subtasks" from dependencies | **Deterministic graph query** (callees + children), no LLM | House law: deterministic first. An LLM task-planner is a later agent tool behind the grouper's two-gate pattern, not a checkbox list (06). |
| "load current node tasks only, or current tab, or all — like the commits" | Board **scope pill** (*This node · This tab · All*): one optional `scope_node_id` on the board read, subtree membership resolved server-side, pill state persisted per workspace tab | The commits view already taught this grammar (`historyScope` per tab; `node_id` param where a `ProjectSchema/` id means all — `versioning/commits.py`). Same muscle memory, same wire shape (03, 04). |
| "easily link task to node and off" | Anchors keyed by `node_id` with **idempotent add/remove** — every surface renders linking as a toggle (popover checkbox, attach search, detail chip) | A toggle is only safe when the operations are idempotent and keyed by the node, not a list index. Double-click can't corrupt; retry can't duplicate (02, 03). |
| "easy way to transfer task from one node to another" | First-class **`anchors/move`** (atomic remove+add, snapshot refresh, system note); drag a popover row onto another node card; *Re-anchor* = the same move with a dead source | Transfer that preserves task history beats detach+reattach; one endpoint serves the drag gesture, the picker, and the unresolved repair flow (02, 05). |
| "backlog should not be on the kanban" | Backlog column gets **`is_backlog`** and the board never renders it; a muted `Backlog 12` link jumps to the List view's backlog section | The kanban is the execution surface; an unbounded pen column drowns the four lanes that mean something. Jira made the same split for the same reason (01, 04). |
| "list table — sprint table above, backlog list below" | **List view**: GitHub-Projects-style table, **Active** section (status-grouped, collapsible) above a hard divide, **Backlog** (rank-ordered) below; drag across the divide = ordinary status move | Planning and executing are different postures; one payload, two projections, zero new endpoints. When sprints land (seam in 06), Active becomes per-sprint tables and nothing else changes shape (04). |
| "add search" | One **search box** for both views: title, `VN-n` key, labels, anchor qnames; `/` to focus; counts gray to `1 of 7`, never silently hide | One input that understands qnames replaces the mock's separate anchored-node box — two adjacent search boxes is a design smell. Client-side over the loaded payload; server `?q=` is a seam (04). |

## What already exists (and is used, not rebuilt)

| Existing | Role here |
|---|---|
| `documents: Set[DocumentSchema]` on every node schema (`core/model/schemas/*.py`) | The attachment precedent — but inverted. Tasks point **at** nodes (soft refs), nodes don't point at tasks, so the parser never has to know tasks exist (01). |
| `CallSchema.target_function` dangling after renames; parser keeps ids of surviving nodes, deletes vanished ones (`core/parser/graph_builder/collection/ast_processor.py`) | Exactly the failure mode anchors are designed around: rename = new id = dangling anchor = **unresolved** (02). |
| House API pattern: `api/v1/*_routes.py` → `core/services/*_service.py` → `core/repository/*_repo.py` (`BaseRepo`, registered in `Repositories`) → `core/model/` + `core/model/schemas/` | Tasks are one more citizen: `task_routes.py`, `TaskService`, `TaskRepo`/`BoardRepo`, `task_schema.py` (03). |
| `scoped_client` (db + branch + ref), UoW `compare_to` | Tasks live **in the project db, on the branch**, like documents and conversations — versioned, commit-batched, undo-able for free. Cross-branch task sharing is a named seam, not v1 (01). |
| `fastapi-cache` (`DEFAULT_TTL`, see `document_routes.py`) + socket/json-rpc layer | Anchor-summary caching and live badge invalidation (03). |
| Frontend: `WorkspaceTabs.tsx` (Code/Docs/Canvas), `EnhancedNode.tsx`/`NodeHeader.tsx` (status dot + diff badge precedent), `NodeContextMenu.tsx` (action union), `SelectNodeDialog.tsx`, `Layout.tsx` rightSidebar slot, sidebar `TreeNode/`, zustand slices + react-query + `@xyflow/react` | Every task surface mounts into a slot that already exists. The board is the only whole-new screen (04, 05). |
| Agent v2 harness + `Agent/tools/registry.ts` coming-soon gating; grouper's review gate; agent-v3's undo-via-commits | The **later** agent seam: `plan_tasks` / `create_task` tools slot in as registry entries with the two-gate flow (06). |

## Dendrogram — the system, top-down

```
task management
│
├── 01 data model             TaskSchema · TaskAnchor subdocument · Board/columns
│   │                         (is_done · is_backlog + protection laws) · task DAG
│   │                         (subtasks · blocked_by) · LexoRank · VN-n keys
│   └── placement             project db, branch-riding · soft refs to nodes · why not
│                             typed links · deletion semantics
├── 02 anchors & hot nodes    anchor lifecycle · idempotent toggle · move/transfer
│   │                         · derived resolution · re-anchor = move with dead source
│   │                         · reparse interplay (no parser hooks in v1)
│   └── convergence           the hot rule (≥2 open through closure, deduped) · one
│                             anchor-summary query · blockers ranking · invalidation
├── 03 api                    routes/service/repo in the house pattern · endpoint table
│                             · board scope param (commits grammar) · anchor
│                             add/remove/move · validation sentences · caching · socket
├── 04 board & list ui        Tasks tab · view switcher (Board · List, per-tab) ·
│   │                         scope pill (This node · This tab · All, per-tab) ·
│   │                         search (/ to focus, both views) · filter bar
│   ├── board view            workflow columns only — backlog never renders ·
│   │                         dnd + optimistic move · card states
│   └── list view             Active (status groups) ↑ · divide · Backlog ↓ ·
│                             drag across the divide · inline add rows · sort
├── 05 detail & canvas ui     right-slot arbitration · detail panel sections · Anchor-
│                             current-node chip · interactive popover (toggle · attach
│                             search · drag-transfer) · hot glow · task lens · sidebar
│                             badges + Blockers section
└── 06 graph & agent          "New task here" modal · suggested subtasks (deterministic)
                              · task context for the agent · future plan_tasks tool
                              · out-of-scope ledger
```

## Decisions (settled here)

1. **Tasks point at nodes; nodes never point at tasks.** Anchors are soft
   string refs + snapshot, stored on the task. The parser, group service, and
   every existing write path stay byte-identical. Task/node join happens in
   task-side queries only.
2. **Resolution and hotness are derived, never stored.** Two reads of the same
   graph state always agree. The only stored anchor fields are `node_id`,
   `qname`, `kind` (snapshot at anchor time, refreshed on re-anchor).
3. **Project db, current branch.** Tasks ride branches and commits like every
   other document. A branch experiment sees its own tasks; promote merges
   them. A branch-agnostic task store is a seam (01), taken up only if real
   usage demands it.
4. **One board per project in v1.** `Board` is a real document (columns are
   editable, `is_done` is per-column) but there is exactly one; multi-board is
   an id away, not a schema change.
5. **The DAG is guarded at the edge.** Adding a subtask or blocked-by edge
   runs a cycle check and refuses with a sentence. Progress and hot counts
   dedupe through the closure — a task reachable twice counts once.
6. **The right slot is exclusive.** Task detail and Agent panel share the
   slot; selecting a task opens detail, closing restores the agent. No
   double-drawer layout.
7. **Suggested subtasks are graph queries.** Callees and children of the
   anchored node, checkbox-picked, each new subtask anchored to its
   dependency. LLM task planning is an agent tool later, behind estimate +
   review gates (06).
8. **Scope follows the commits grammar.** One optional `scope_node_id` on the
   board read; absent (or the project id) = all, otherwise the node's subtree,
   resolved server-side. The pill state persists per workspace tab exactly
   like `historyScope`. Default is *This tab* — the board you see matches the
   code you're looking at.
9. **Linking is idempotent and keyed by node.** Anchor add/remove take a
   `node_id`, never a list index; adding an existing anchor or removing an
   absent one is a no-op, which is what makes every surface a safe toggle.
   Transfer is a first-class atomic `move` recorded in activity; re-anchor is
   `move` where the source is dead.
10. **Backlog is a pen, not a workflow stage.** Exactly one protected
    `is_backlog` column per board (rename-only; mutually exclusive with
    `is_done`). The kanban never renders it; the List view's bottom section
    owns it; crossing the divide is an ordinary status move. Backlog tasks
    still count as open — parked work converging on a node is still the
    blocker signal.
11. **Two views, one payload, one mutation set.** Board and List are
    projections of the same query cache sharing the same move/create
    mutations — a view is never a second data path. View choice, scope, and
    collapse state persist per workspace tab.
12. **One search box.** Title, key, labels, and anchor qnames through a
    single client-side predicate shared by both views; `/` focuses it. The
    mock's separate anchored-node input folds into it. Server search is a
    seam, and the input's contract doesn't change when it lands.

## Implementation status (2026-07-18)

T1–T2 landed with two behavior bugs, and T3 landed as a skeleton. The audit
of the shipped code against this plan — three root-caused bugs (browser
cache staleness, per-task routes 404ing on `TaskSchema/…` ids, the New-task
modal unmounted outside the Tasks tab) plus the catalogue of skipped
surfaces — lives in **[`fixes/`](fixes/README.md)**, with fix order and
verification gates. 03 carries two inline corrections learned from it.

## Build order

Each phase ends runnable; later phases only add.

| Phase | Contents | Demo gate |
|---|---|---|
| **T1 — Data + API core** | `task_schema.py` + models · `TaskRepo`/`BoardRepo` in `Repositories` · `TaskService` (CRUD, move, DAG-validated edges, idempotent anchor add/remove + `anchors/move`) · board `scope_node_id` resolution · `task_routes.py` under `/tasks` · default board bootstrap | HTTP tests: create the mock's board (epic + shared subtask + blocked pair), move a card, cycle refused with its sentence, scoped board read returns only the subtree's tasks |
| **T2 — Board + List UI** | `Tasks` tab in `WorkspaceTabs` · `features/Dashboard/features/Tasks/` · **view switcher** · board view (workflow columns only, backlog link-out) · **list view** (Active groups ↑ / Backlog ↓, drag across the divide, inline add) · **search** (`/`, shared predicate) · **scope pill wired to the tab, `historyScope`-style** · react-query hooks + optimistic move · New-task modal (title/type/priority, anchor pre-filled from the tab's active node) | The corrected mock, live: board shows four columns with `Backlog 2` as a link; flip to List, drag *Add runner tests* across the divide into To do and watch it appear on the board; type `dd` in search and both views narrow; flip This tab ↔ All and counts change |
| **T3 — Anchors + detail + canvas** | anchor-summary · detail panel in the right slot (all sections except activity) · **Anchor-current-node chip** · canvas badge + **interactive popover (link toggles + Attach search)** · sidebar badges · "New task here" context action with pre-filled anchor + suggested subtasks | Two tasks on `main.dd` → amber everywhere; check/uncheck a popover toggle and watch the badge count follow; detail panel round-trips subtask toggles |
| **T4 — Convergence polish** | hot glow styling · task lens · Blockers sidebar section · **drag-transfer from popover to node card** + Move picker · re-anchor flow (unresolved state + candidate picker) · activity/notes · anchored-node board filter · cache invalidation over socket | Drag a task row from `dd`'s popover onto `runner` → anchor moves, both badges update, activity says so; rename a function on disk → anchor shows ⚠, re-anchor fixes it; lens dims the canvas to the task's nodes |
| **T5 — Agent seam** (separate effort) | task context block in the context factory · `plan_tasks` tool behind the two-gate pattern · registry entry | Out of this plan's demo path; specced in 06 |

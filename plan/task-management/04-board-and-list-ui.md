# 04 — Board & List UI (the Tasks tab)

The one whole-new screen: a single Tasks tab with **two views over one
payload** — **Board** (kanban, workflow columns only) and **List**
(GitHub-Projects-style table: active work on top, backlog at the bottom).
Everything else in 05 mounts into existing slots; this feature folder follows
the mock (`V-NOC Tasks.dc.html`) pixel-for-pixel where the mock is right, and
this doc where it was hand-waving or wrong — the mock has no list view and
puts Backlog on the kanban, which this plan corrects.

## Where it mounts

`WorkspaceTabs.tsx` gains a fourth trigger after Canvas:

```
Code | Docs | Canvas | Tasks
```

Same `TabsTrigger` styling block as its siblings (the mock's pill-tabs are the
Claude-design idiom, not ours — keep the existing shadcn `Tabs` look). The
trigger shows the open-task count badge (`Tasks 6`) **for the tab's current
scope** from the board query. `TabsContent value="tasks"` renders the feature
root.

## Scope — the board follows the tab, like commit history

The board is **node-aware per workspace tab**, copying the pattern the
commits view already shipped (`historyScope` per tab in `Main/index.tsx` →
`useCommitHistory(projectId, scopeId)` → `node_id` param where a
`ProjectSchema/` id means everything):

| Scope | Meaning | `scope_node_id` sent |
|---|---|---|
| **This node** | tasks anchored to the tab's *active* node only (`activeNodeId[tabId]`, falling back to the tab's root node) | the active node id |
| **This tab** *(default)* | tasks anchored anywhere under the tab's root node — subtree resolved server-side | the tab's root node id |
| **All** | every task on the board | omitted (or the project id, commits-style) |

- Rendered as a three-segment pill, **first control in the filter bar** —
  scope is where you look, filters are what you hide, so scope comes first.
- State lives in `tasksSlice.taskScope: Record<tabId, 'node' | 'tab' | 'all'>`
  (per-tab keyed records, same shape as `uiSlice.activeNodeId`), so each
  workspace tab remembers its own scope — exactly how `historyScope` behaves.
- Scope changes are a react-query key change
  (`['tasks','board',projectId,branch,scopeNodeId]`) — no client-side subtree
  math, the server owns membership (03).
- Column headers show scoped counts; the summary reads
  `4 of 6 open · 1 hot node` when scoped so the hidden remainder is never a
  mystery. Creating a task while scoped pre-fills its anchor from the scope
  node (see NewTaskModal below).

## Two views, one payload — Board and List

A **view switcher** (`Board | List`, GitHub-Projects style segmented control)
sits at the far left of the filter bar. Both views render the same board
query and share the same mutations — a view is a projection, never a second
data path. Choice persists per tab (`taskView` in the slice).

### Board view — workflow columns only

The kanban **never renders the backlog column** (`is_backlog`, 01). Backlog
on a board is dead weight: it is unbounded, unordered work that drowns the
four columns that mean something. The board is the *execution* surface:

```
To do | In progress | In review | Done
```

- The board header's `+ New task` and each column's `+` create into that
  column (`To do` for the header button) — never into backlog.
- Dragging a card off the board into backlog is not a board gesture; parking
  work is a List-view act (below) or the detail panel's status dropdown,
  which always lists every column including Backlog.
- Backlog tasks still exist in the payload (scope, search, hot counts all see
  them); the board simply doesn't paint them. `Backlog 12` appears as a muted
  link at the right end of the column row — click switches to List scrolled
  to the backlog section, so the parked work is one click away, never a
  mystery.

### List view — Active above, Backlog below

The Jira backlog-screen shape, with GitHub Projects' table density:

```
▾ ACTIVE (5)                            ← tasks in workflow columns
    ▾ To do (1)          [status group rows, collapsible]
        VN-15  Speed up runner   improvement  ▍▍▍ medium  perf   ƒ main.runner +1   ⊘
    ▾ In progress (2)
        VN-12  Fix logging bug   bug          ▍▍▍ high    logging  ƒ main.dd   ✓0/1
        …
    ▸ Done (1)                    [done group collapsed by default]
  + Add task                       → creates in To do
────────────────────────────────── the divide ──────────────────────────────────
▾ BACKLOG (2)                           ← the pen, rank-ordered
    VN-9   Refactor main module  epic   tech-debt   ≣ main   ✓1/3
    VN-13  Add runner tests      task   ƒ main.load_config ⚠
  + Add task                       → creates in Backlog
```

- **Row anatomy**: key (mono, muted) · title · type badge · status (inline
  dropdown → `move`) · priority bars · label chips · anchor chips (same
  `AnchorChip`, same jump-to-canvas click) · progress / blocked / ⚠ markers ·
  updated. Row click opens the detail panel; every cell that edits uses the
  same mutations as the board.
- **Drag across the divide** is the point of the layout: Backlog row → Active
  (lands in To do, or on a specific status group to target it) and Active row
  → Backlog. It is the same `move` mutation as a board drag — status +
  LexoRank midpoint, optimistic. Within the backlog section, drag reorders
  rank (backlog is a column, so ranking already works, 01).
- **Sortable headers** (updated / priority / key) sort *within* groups,
  client-side; drag-reorder is disabled while a sort is active (the two
  contradict — GitHub Projects makes the same call).
- Section and group collapse state is per-tab UI state, not persisted server
  data.
- "Sprint" is what the Active section becomes when sprints land (06's seam):
  one Active table per sprint, backlog still the bottom section. The divide
  ships now and survives that upgrade unchanged.

### Search

A real task search, both views, GitHub placement (in the filter bar, before
the type control):

- Matches **title, `VN-n` key, labels, anchor qnames, and description** —
  case-insensitive substring over the loaded payload; one predicate in
  `useTaskFilters` shared by board and list.
- `/` focuses it from anywhere in the Tasks tab (GitHub muscle memory);
  `Esc` clears. Placeholder: `Search tasks…  ( / )`.
- Board: non-matching cards unrender, column counts gray to `1 of 7`.
  List: non-matching rows unrender, group counts follow; empty groups hide.
- The anchored-node *scope* search box from the mock folds into this one
  input — one search that also understands qnames beats two adjacent boxes
  (the `e.g. main.dd` hint moves into the placeholder rotation).
- Server-side search is a named seam for when boards outgrow the one-payload
  model; the input's contract (debounced query string) doesn't change.

## Feature folder

House conventions (feature folder + components/hooks/service, react-query for
server state, zustand slice for UI state):

```
features/Dashboard/features/Tasks/
├── index.tsx                    TasksRoot: filter bar + view switcher + active view
├── components/
│   ├── board/
│   │   ├── BoardView.tsx        workflow columns row — never renders is_backlog
│   │   ├── BoardColumn.tsx      header (dot · title · count · "+") + card list + drop target
│   │   └── TaskCard.tsx         the compact card, all states
│   ├── list/
│   │   ├── ListView.tsx         Active section ↑ · divide · Backlog section ↓
│   │   ├── TaskTable.tsx        status-grouped table, sortable headers, collapse
│   │   ├── TaskRow.tsx          key · title · badges · inline status · anchors · markers
│   │   └── InlineAddRow.tsx     "+ Add task" per section (To do / Backlog)
│   ├── TaskTypeBadge.tsx        bug/improvement/epic/task chip (shared with 05)
│   ├── PriorityBars.tsx         the 3-bar indicator (shared with 05)
│   ├── AnchorChip.tsx           `ƒ main.dd` pill — normal / hot / unresolved (shared with 05)
│   ├── FilterBar.tsx            view switcher · scope pill · search · type control · summary · + New task
│   └── NewTaskModal.tsx         create flow — anchor pre-filled from the tab's active/scope node (T2: fields; T3: + suggested subtasks, 06)
├── hooks/
│   ├── useBoardDnd.ts           drag state + midpoint rank computation (board columns AND list sections)
│   └── useTaskFilters.ts        client-side search + filter predicate (shared by both views)
└── service/
    └── useTasks.ts              react-query: board query · anchor-summary query · all mutations
```

## Data layer

- **react-query** (`@tanstack/react-query`, already in the app) owns server
  state: `['tasks','board',projectId,branch]` and
  `['tasks','anchor-summary',projectId,branch]`. Socket events
  `tasks.changed` / `tasks.summary_changed` (03) invalidate these keys — the
  same pattern the rest of the app uses for live refresh.
- **zustand slice** (`store/slices/tasksSlice.ts`, joined into the existing
  `ProjectStore` union next to `uiSlice`) owns UI state only:

  ```ts
  selectedTaskId: string | null                      // detail panel (05)
  lensTaskId: string | null                          // task lens (05)
  taskScope: Record<string, 'node' | 'tab' | 'all'>  // per-tab scope pill
  taskView: Record<string, 'board' | 'list'>         // per-tab view switcher
  listCollapse: Record<string, string[]>             // per-tab collapsed groups
  filters: { query, type, label, priority }          // query = the search input
  ```

  Nothing server-derived goes in the slice; the board renders from the query
  cache, filtered through `useTaskFilters`.

## Drag & drop

**Native HTML5 DnD in v1**, exactly as the mock implements it (draggable card,
column `onDragOver`/`onDrop`), wrapped in `useBoardDnd` — which also serves
the List view: a table row drags the same way, and a status group or the
backlog section is just another drop target resolving to (status, rank):

- On drop: compute LexoRank midpoint between neighbor cards client-side, fire
  the `move` mutation **optimistically** (react-query `onMutate` cache patch,
  rollback on error — the server re-validates rank and column).
- Dragging state: `opacity .35 / dashed border` on the source card; drop
  target column gets the green-tinted border (mock values).
- `@dnd-kit` is the named upgrade path (keyboard DnD, cross-column previews,
  column reordering) — one new dependency, deferred until a real need, since
  the board's DnD surface is small and the mock's behavior is fully covered.

## The task card — states

Base: title row + meta row (type badge, label chips, progress, blocked) +
anchor-chip row. Mock's density and values are the spec; states:

| State | Treatment |
|---|---|
| default | dark card, thin border (`#1a1c21` / `#23262c` family → theme vars) |
| hover | border + background lighten one step; cursor grab |
| dragging | opacity .35, dashed border (source); green column highlight (target) |
| blocked | `⊘ blocked` red-tinted pill — derived field from the API, never computed client-side |
| subtasks | `✓ 2/5` mono counter (closure-deduped number from the API) |
| unresolved anchor | the anchor chip carries `⚠` amber suffix; card otherwise normal |
| hot anchor | anchor chip flips to the amber treatment (data from anchor-summary) |

Anchor chip click **stops propagation** and jumps to canvas: switch workspace
tab to `canvas`, focus + auto-expand the node (existing `focusSlice` +
`useAutoExpandToNode` actions). Card click opens the detail panel (05).

## Filter bar

Left-to-right: **view switcher** (Board · List), **scope pill** (This node ·
This tab · All — see Scope above), **search input** (see Search above — one
box for titles, keys, labels, and anchor qnames), type segmented control
(All/bug/task/improvement/epic), spacer, board summary (`6 open · 1 hot
node`, or `4 of 6 open` when scoped — open count from board query, hot count
from anchor-summary), green `+ New task` button. Label and priority filters
live in a small dropdown appended to the segmented control rather than
inflating the bar (mock omitted them; checklist requires them).

Filtering is a pure client-side predicate over the board payload; a filtered
column still shows its true total count grayed (`3 of 7`) so filters never
silently hide work.

## Column header

Dot (column color) · title · count · `+` (opens NewTaskModal pre-set to that
column). Column management (rename, recolor, `is_done`, delete-with-move) is a
small settings popover on the header — v1 scope is exactly what
`PATCH /tasks/board` supports, nothing more. The backlog column never appears
here (board view skips it); its management surface is the List view's section
header, and the column itself is protected (rename-only, 01).

## Visual language

Follow the app, not the mock's hex literals: reuse the existing theme vars
(`--background-color`, border tokens) and shadcn components (`Tabs`,
`ContextMenu`, dialog primitives) so the tab reads native. The mock's specific
accents that ARE the design and should be lifted as tokens into the Tasks
feature: type colors (bug `#e07a7a` red, improvement `#4ecdc4` teal, epic
`#a78bfa` purple, task gray), priority bar colors, the amber hot family
(`#e2a03f`), the green anchor-chip family. Define once in
`Tasks/theme.ts` (the Agent feature's local-theme precedent), consume from
board and canvas surfaces alike so hot-amber is one constant everywhere.

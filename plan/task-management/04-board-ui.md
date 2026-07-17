# 04 — Board UI (the Tasks tab)

The one whole-new screen. Everything else in 05 mounts into existing slots;
the board gets its own feature folder and follows the mock
(`V-NOC Tasks.dc.html`) pixel-for-pixel where the mock is right, and this doc
where it was hand-waving.

## Where it mounts

`WorkspaceTabs.tsx` gains a fourth trigger after Canvas:

```
Code | Docs | Canvas | Tasks
```

Same `TabsTrigger` styling block as its siblings (the mock's pill-tabs are the
Claude-design idiom, not ours — keep the existing shadcn `Tabs` look). The
trigger shows the open-task count badge (`Tasks 6`) from the board query.
`TabsContent value="tasks"` renders the feature root. The board is
project-level, not node-level — it ignores `nodeId` and renders the same
content in every workspace tab instance.

## Feature folder

House conventions (feature folder + components/hooks/service, react-query for
server state, zustand slice for UI state):

```
features/Dashboard/features/Tasks/
├── index.tsx                    TasksBoard root (filter bar + columns row)
├── components/
│   ├── BoardColumn.tsx          header (dot · title · count · "+") + card list + drop target
│   ├── TaskCard.tsx             the compact card, all states
│   ├── TaskTypeBadge.tsx        bug/improvement/epic/task chip (shared with 05)
│   ├── PriorityBars.tsx         the 3-bar indicator (shared with 05)
│   ├── AnchorChip.tsx           `ƒ main.dd` pill — normal / hot / unresolved (shared with 05)
│   ├── FilterBar.tsx            type segmented control · anchored-node search · summary · + New task
│   └── NewTaskModal.tsx         create flow (T2: fields only; T3: + anchors + suggested subtasks, 06)
├── hooks/
│   ├── useBoardDnd.ts           drag state + midpoint rank computation
│   └── useTaskFilters.ts        client-side filter predicate
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
  selectedTaskId: string | null        // detail panel (05)
  lensTaskId: string | null            // task lens (05)
  filters: { type, label, priority, anchorQuery }
  ```

  Nothing server-derived goes in the slice; the board renders from the query
  cache, filtered through `useTaskFilters`.

## Drag & drop

**Native HTML5 DnD in v1**, exactly as the mock implements it (draggable card,
column `onDragOver`/`onDrop`), wrapped in `useBoardDnd`:

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

Left-to-right, per the mock: type segmented control (All/bug/task/improvement/
epic), anchored-node search input (matches against anchor qnames, mono
placeholder `e.g. main.dd`), spacer, board summary (`6 open · 1 hot node` —
open count from board query, hot count from anchor-summary), green `+ New
task` button. Label and priority filters live in a small dropdown appended to
the segmented control rather than inflating the bar (mock omitted them;
checklist requires them).

Filtering is a pure client-side predicate over the board payload; a filtered
column still shows its true total count grayed (`3 of 7`) so filters never
silently hide work.

## Column header

Dot (column color) · title · count · `+` (opens NewTaskModal pre-set to that
column). Column management (rename, recolor, `is_done`, delete-with-move) is a
small settings popover on the header — v1 scope is exactly what
`PATCH /tasks/board` supports, nothing more.

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

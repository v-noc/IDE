# v2 · 02 — Board (filter bar · 5 columns · task card · DnD)

Mock region: `data-screen-label="Tasks board"`. Tokens per
[01-design-tokens.md](01-design-tokens.md).

## Filter bar (one row, `padding:10px 16px`, bottom border `border.subtle`)

Left → right, `gap:8px`:

1. **Type segmented control** — container `bg #15161a`, border
   `border.input`, radius 8px, inner padding 3px, `gap:3px`. Buttons:
   `All · bug · task · improvement · epic`, 11.5px/550, padding `5px 11px`,
   radius 6px. Active: `bg #2c2f36, color #f0f2f5`; inactive: transparent,
   `#8b919d`. (Filter is client-side over the board payload — unchanged.)
2. **Anchored-node filter input** — width 220px, **JetBrains Mono 11.5px**,
   `bg #15161a`, border `border.input`, radius 8px, padding `6px 10px`.
   Placeholder: `Filter by anchored node…  e.g. main.dd`. Predicate:
   case-insensitive substring over each task's anchor qnames (a task with no
   anchors never matches a non-empty filter). This is a separate input by
   design — do not fold it into a general search box.
3. **Spacer**, then **board summary** — 11px `#5c6270`, right-aligned:
   `{openCount} open · {hotCount} hot node{s}`. Open = tasks not in an
   `is_done` column (mock: `status !== 'done'`); hot count from the
   anchor-summary query. Hide the `· … hot node` suffix when zero.
4. **`+ New task`** — `green.btn` (bg `#2c9a58`, border `#2f9d5c`, text
   `#0b1a10`, 12px/650, padding `6px 12px`, radius 8px, hover `#34ab63`).
   Opens the modal; pre-fills per `../fixes/03`.

## Columns — all five render

Row: `display:flex; gap:12px; padding:14px 16px; overflow-x:auto`.

Per column (mock `COLUMNS` order — **Backlog first**, then To do,
In progress, In review, Done):

- Shell: `width:252px; min-width:252px; border-radius:11px;
  bg #141518; border 1px #1d1f24; max-height:100%`.
- **Drag-over state** (only while a card drag is live):
  bg `rgba(62,207,114,.04)`, border `rgba(62,207,114,.35)`.
- Header (`padding:10px 12px 8px`): 7px color dot (per-column, 01) ·
  title 12px/650 `#dfe2e7` · count mono 10px `#5c6270` (count respects the
  active filters, shown as plain `n`) · `+` button pushed right (14px,
  `#5c6270` → hover `#9ba1ab`) opening the modal preset to this column.
- Card list: `padding:2px 8px 10px; gap:7px; overflow-y:auto`.

This is the v1→v2 reversal: **Backlog is an ordinary column again** — a
drag into it parks work, a drag out resumes it. No `Backlog n` link, no
List view in v2. `is_backlog` stays in the schema (protection laws, "open"
semantics unchanged); the board just no longer hides the column.

## Task card

Shell: `padding:11px 12px; radius:10px; bg #1a1c21; border 1px #23262c;
cursor:grab; flex column; gap:8px`. Hover: `border #33373f; bg #1e2026`.
Dragging (source): `opacity:.35; border-style:dashed`. Click → opens the
detail panel (`selectedTaskId`).

Three stacked rows, all optional parts collapse:

1. **Title row** — title 12.8px/550, `line-height:1.4`, `#e6e8ec`,
   `flex:1`; **priority bars** top-right (01: 3px-wide bars 5/8/11px, lit
   in priority color, unlit `#2c2f36`; `title` tooltip `"{prio} priority"`;
   `none` renders nothing).
2. **Meta row** (`flex-wrap; gap:5px`) — type chip (01) · label chips
   (10px/550 `#9ba1ab` on `#22252b`) · subtask progress
   `✓ {done}/{total}` (9px check SVG + mono 10px `#8b919d`; hidden when no
   subtasks) · `⊘ blocked` pill (01; shown when any blocker is open —
   derived field from the API, never computed client-side).
3. **Anchor row** (`flex-wrap; gap:4px`, hidden when no anchors) — one
   **anchor chip** per anchor: mono 10px, `{kindIcon} {qname}`, padding
   `2px 7px`, radius 5px.
   - Resolved: `green.chip`. Hot (≥2 open tasks on the node, from
     anchor-summary): `amber.text` on `amber.bg`, border
     `rgba(226,160,63,.35)`.
   - Unresolved: normal chip + ` ⚠` suffix in `#e2a03f`.
   - Tooltips (mock): unresolved → `Unresolved — code changed under this
     task`; hot → `Hot node — multiple open tasks converge here`; else →
     `Jump to node on canvas`.
   - Click **stops propagation** and jumps: switch workspace tab to
     canvas + focus the node. Hover: `filter:brightness(1.2)`.

## Drag & drop (native HTML5, per the mock's handlers)

- Card: `draggable`; `onDragStart` sets `effectAllowed='move'` **and**
  `dataTransfer.setData('text/plain', task.id)` (mock omits setData; add it
  — Firefox won't start a drag without it) and stores `dragging`.
  `onDragEnd` clears `dragging` + `dragOverCol`.
- Column: `onDragOver` → `preventDefault()` + set `dragOverCol` (the
  green treatment above). `onDrop` → `preventDefault()`; move the task to
  the column (real build: LexoRank midpoint at drop position + optimistic
  `move` mutation, rollback + **error toast** on failure — `../fixes/02`).
- Drop on the card's own column with no reorder = no-op.

## Empty states

- Column with no matching cards: header renders, list is empty — no
  placeholder art (the mock shows none).
- Filters active: column counts show the filtered number; cards simply
  unrender. (The v1 `3 of 7` grayed-count idea is an enhancement, not in
  the mock — skip for v2 fidelity.)

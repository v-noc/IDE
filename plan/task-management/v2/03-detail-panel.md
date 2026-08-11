# v2 · 03 — Task Detail Panel (all nine sections)

Mock region: `data-screen-label="Task detail panel"` + `detailVM()`. This is
the doc that answers "where is the title edit / description / updated /
node" — the mock has all of them; v1 shipped none. Every field below is
already on the wire (`_enrich_task` — see [05](05-gap-closure.md)), so this
is pure frontend build, gated only on `../fixes/02` (routes) for the writes.

## Shell

- `width:384px; min-width:384px; border-left:1px solid #22252b;
  bg #141518` — mounted in the exclusive right-sidebar slot (unchanged).
- **Header** (h 44px, `padding:0 16px`, bottom border `#1e2026`, gap 8px):
  type chip (01) · task key mono 10.5px `#5c6270` (`VN-9`) · `✕` pushed
  right (15px `#8b919d`; hover `#e6e8ec` on `#22252b`, radius 6px).
  Keep v1's ← back button before the type chip when the nav stack is
  non-empty (panel navigation, bottom of this doc).
- **Body**: `flex:1; overflow-y:auto; padding:16px; flex column; gap:18px`.
  Section headings all share one style: 10.5px, 700,
  `letter-spacing:.08em`, `#6b7280`, uppercase text.

## 1 · Title — borderless input, edit in place

```
font-size:16.5px; font-weight:650; color:#f0f2f5;
background:transparent; border:1px solid transparent; border-radius:8px;
padding:6px 8px; margin:-6px -8px 0;      ← negative margin: text aligns
                                             with the panel edge until hover
hover:  border-color:#26292f;
focus:  border-color:#3ecf72; background:#15161a;
```

Invisible at rest, input-shaped on hover, green-ringed while editing.
Commit: PATCH `{title}` on blur **and** Enter (mock patches on change;
the real build debounces to blur/Enter). Escape reverts to the last saved
value. Empty title → revert, never save `""`.

## 2 · Fields grid — 2×2 read-only tiles

`display:grid; grid-template-columns:1fr 1fr; gap:8px`. Tile:
`bg #15161a; border 1px #26292f; radius 8px; padding:8px 10px`, label
9.5px/700/`.07em` `#6b7280` over value 12.5px/550.

| Tile | Value | Color |
|---|---|---|
| STATUS | column title, preceded by a 7px column-color dot | `#dfe2e7` |
| PRIORITY | priority name (`none` included) | priority color; `#6b7280` for none |
| CREATED | short date (`jul 13` style — lowercase `MMM D`) | `#9ba1ab` |
| UPDATED | short date | `#9ba1ab` |

Read-only in v2 (the mock renders spans, not controls; status changes are
board drags — Backlog is on the board again, 02). *Enhancement seam, not
v2:* STATUS tile opens a column menu → `move`.

## 3 · Labels — chip row

Directly under the grid with `margin-top:-8px` (mock tucks it against the
grid). Chips 10.5px/550 `#9ba1ab` on `#22252b`, border `#2c2f36`, padding
`3px 9px`, radius 99px. Hidden entirely when the task has no labels.
Read-only in v2 (mock has no add/remove affordance).

## 4 · Description — prose box

Heading `DESCRIPTION`, then a box: 12.5px, `line-height:1.65`, `#c3c8d1`,
`bg #15161a`, border `#26292f`, radius 9px, padding `11px 13px`. Render the
stored description as plain text with paragraph breaks (the mock is plain
text — no markdown toolbar, no code styling).

Editing (the mock shows the read view only; the panel must not be a dead
end): click the box → swap to a textarea with identical metrics, focus
border `#3ecf72`; PATCH on blur; Esc cancels. Empty description renders the
box with placeholder-colored text `Add a description…` (`#5c6270`).

## 5 · Anchored nodes — bordered row list

Heading `ANCHORED NODES`. Container: border `#22252b`, radius 9px,
`overflow:hidden`; rows separated by bottom border `#1e2026`, row padding
`9px 12px`, gap 8px:

- kind icon — mono 10px in its kind color (01), 13px wide, centered
- qname — **mono 12px** `#dfe2e7`
- state chips: hot → `hot · {n} tasks` amber chip (01); unresolved →
  `⚠ unresolved` 9.5px/650 `#e2a03f` (bare text, no pill)
- actions pushed right (`gap:6px`):
  - resolved → **`Show on canvas`**: 10.5px, `#9ba1ab` on `#1f2126`,
    border `#2c2f36`, padding `3px 9px`, radius 6px; hover `#e6e8ec` on
    `#26292f`. Switches to canvas + focuses the node.
  - unresolved → **`Re-anchor`**: 10.5px/600 `#e2b95a` on
    `rgba(226,160,63,.1)`, border `rgba(226,160,63,.4)`; hover bg `.18`.
    Opens the candidate picker (existing flow).
- unresolved rows get row bg `rgba(226,160,63,.04)`.

Zero anchors: render the container with one placeholder row (`#5c6270`,
`No anchored nodes`) — never a floating heading over nothing (the v1
screenshot bug). The add-anchor affordance lives in `../fixes/03`; when
built it appends a final `+ Add anchor` row here, styled like the dashed
buttons in section 6.

## 6 · Subtasks — checklist with progress

Heading: `SUBTASKS · {done}/{total}` (direct children; done = child in an
`is_done` column). **Section renders whenever the task has subtasks; the
two buttons below render always** — an empty-subtask task still shows
`+ Add subtask` / `✦ Suggest…` (heading shows `0/0` or is omitted, match
the mock's `hasSubtasks` guard for the list itself).

Row list (same bordered-container recipe as §5), row `padding:8px 12px;
gap:9px`, hover bg `#17191d`:

- **Checkbox** 16×16, radius 5px: done → `bg #2c9a58; border #2f9d5c;
  color #0b1a10` with `✓` 10px; not done → `bg #1a1c21; border #33373f;`
  glyph transparent. Click toggles the child between its column and Done
  (mock: `status = isDone ? 'todo' : 'done'` → real build: first `is_done`
  column ↔ first workflow column; optimistic).
- **Title** 12.5px/550, button-styled text: done → `#6b7280` +
  `line-through`; open → `#dfe2e7`. Hover `#7fdba3`. Click navigates the
  panel to the child (nav stack push).
- **`⑂ shared` chip** (01) when the child has >1 parent, tooltip
  `Shared — has multiple parent tasks`.
- **Status** pushed right, mono 9.5px `#5c6270` (`Done`, `In progress`,
  `Backlog` — column titles).

Buttons row (`gap:8px`):

- `+ Add subtask` — dashed border `#2c2f36`, transparent bg, `#8b919d`,
  11.5px, padding `6px 11px`, radius 7px; hover `#e6e8ec` /
  border `#3a3e46`. Click → inline title input in place → create-and-link
  (existing `addSubtask` inline payload).
- `✦ Suggest from dependencies` — dashed `rgba(62,207,114,.3)`, text
  `#61c98a`; hover bg `rgba(62,207,114,.06)`. Opens the checkbox list from
  the suggest endpoint seeded by the first resolved anchor; checked rows
  create-and-link, each anchored to its dependency (v1 06 semantics).

## 7 · Dependencies — direction-labeled rows

Heading `DEPENDENCIES`. Only when `blocked_by ∪ blocks` is non-empty.
Free-standing rows (`gap:5px`, not a bordered container): each row a
button — `bg #15161a; border #26292f; radius 8px; padding:8px 11px;
gap:8px`; hover border `#33373f`:

- direction label, 10px/650, `min-width:70px`: `blocked by` in `#e07a7a` ·
  `blocks` in `#e2a03f`
- small type chip (9px variant, 01)
- title 12px/550 `#e6e8ec`
- status pushed right, mono 9.5px `#8b919d`

Order: all `blocked by` rows, then all `blocks` (mock concatenates in that
order). Click navigates the panel (nav stack). `blocks` is derived
server-side; if it arrives as bare ids, resolve titles from the board
payload client-side until the API enriches it.

## 8 · Activity — feed + note input

Heading `ACTIVITY`. Entries (`gap:9px`, 11.5px, `line-height:1.5`): 6px
dot `#2c2f36` at `margin-top:5px` · text `#8b919d` with trailing timestamp
mono 10px `#5c6270` (`moved to In progress jul 15`). System and user notes
interleave chronologically; render even when empty (input always shows).

Input: full-width, `bg #15161a`, border `#26292f`, radius 8px, padding
`8px 11px`, 12px; placeholder `Add a note…`; focus border `#3ecf72`.
Enter submits → notes endpoint → optimistic append.

## 9 · Panel navigation

Subtask and dependency clicks re-target the panel in place, pushing the
previous task id onto a local stack: `←` (header) pops, `✕` always closes.
Preserved from v1 — the mock swaps `selected` directly, but DAG hopping
without a back affordance strands the user (this is the one deliberate
addition to the mock, carried over from v1 05).

## Removed from v1's shipped panel

The `Focus on canvas` button next to the note input is **not in the mock**
— remove it (and the lens entry point) until the lens ships with its exit
bar (`../fixes/04`). The note input is full-width, as designed.

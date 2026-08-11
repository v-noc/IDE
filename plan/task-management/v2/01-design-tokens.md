# v2 · 01 — Design Tokens (from the mock, verbatim)

Everything below is lifted from `V-NOC Tasks.dc.html`. Centralize in
`features/Tasks/theme.ts` and consume everywhere — board, detail panel,
canvas badges, sidebar chips. No raw hex in components; no Tailwind
semantic-color classes standing in for these values.

## Surfaces

| Token | Value | Mock usage |
|---|---|---|
| `bg.app` | `#101113` | page + board background |
| `bg.chrome` | `#141518` | top bar, columns, **detail panel** background |
| `bg.sidebar` | `#131417` | left sidebar |
| `bg.canvas` | `#0e0f11` + `radial-gradient(#212329 1px, transparent 1px)` `22px 22px` | canvas dot grid |
| `bg.card` | `#1a1c21` | task card |
| `bg.node` | `#191b1f` | canvas node card |
| `bg.nodeHeader` | `#20232a` | canvas node header strip |
| `bg.input` | `#15161a` | inputs, field tiles, description box, dep rows |
| `bg.inset` | `#191b1f` | sidebar search input |
| `bg.popover` | `#1d1f24` | node task popover |
| `bg.chip` | `#22252b` | neutral chips, active tab, hover close-btn |
| `bg.hover` | `#1c1e23` / `#26292f` | tree row hover / popover row + button hover |

## Borders

| Token | Value | Usage |
|---|---|---|
| `border.subtle` | `#1d1f24` | chrome dividers, column border |
| `border.panel` | `#22252b` | detail-panel left border, section list borders |
| `border.row` | `#1e2026` | rows inside bordered lists (anchors, subtasks) |
| `border.input` | `#26292f` | inputs, field tiles, description box |
| `border.card` | `#23262c` | task card |
| `border.chip` | `#2c2f36` | neutral chips, popover border |
| `border.strong` | `#33373f` | card hover, undone checkbox, node ▾ button |

## Text

| Token | Value | Usage |
|---|---|---|
| `text.primary` | `#e6e8ec` | body/titles |
| `text.bright` | `#f0f2f5` | detail title input, active tab |
| `text.heading` | `#dfe2e7` | column titles, anchor qnames, field values |
| `text.body` | `#c3c8d1` | description prose |
| `text.secondary` | `#c9cdd4` | tree labels |
| `text.muted` | `#9ba1ab` | task-type chip, buttons, meta |
| `text.dim` | `#8b919d` | inactive tabs, activity text, counts |
| `text.faint` | `#5c6270` | placeholders, mono statuses, timestamps |
| `text.label` | `#6b7280` | **section headings** (DESCRIPTION, SUBTASKS…) |
| `text.disabled` | `#4a4f58` | disabled tabs |

## Greens (the V-NOC accent family)

| Token | Value | Usage |
|---|---|---|
| `green.core` | `#3ecf72` | function ƒ icon, focus borders, column dot (In progress) |
| `green.btn` | `#2c9a58` bg / `#2f9d5c` border / text `#0b1a10` | `+ New task`, done checkbox; hover bg `#34ab63` |
| `green.link` | `#61c98a` (hover `#7fdba3`) | links, ✦ Suggest button |
| `green.chip` | text `#8fd4a8` · bg `rgba(62,207,114,.07)` · border `rgba(62,207,114,.2)` | anchor chip (resolved), green count badges |
| `green.focusRing` | `rgba(62,207,114,.6)` border + `0 0 0 3px rgba(62,207,114,.15)` shadow | focused canvas node |
| `green.dragOver` | bg `rgba(62,207,114,.04)` · border `rgba(62,207,114,.35)` | column drop target |

## Hot amber (one family, four surfaces)

| Token | Value |
|---|---|
| `amber.core` | `#e2a03f` (dot, In-review column dot, ⚠ glyphs) |
| `amber.text` | `#e2b95a` (hot chips, Re-anchor button text) |
| `amber.bg` | `rgba(226,160,63,.1)` (`.12` node badge, `.04` unresolved row bg) |
| `amber.border` | `rgba(226,160,63,.3)`–`.4` (`.35` chips, `.5` hot node border) |
| `amber.glow` | `@keyframes hotGlow` 2.6s ease-in-out infinite: `box-shadow 0 0 0 1px rgba(226,160,63,.35), 0 0 18px rgba(226,160,63,.12)` ↔ `0 0 0 1px …,.55, 0 0 26px …,.22` — static border fallback under `prefers-reduced-motion` |

## Task types (`TYPES`)

`[label, color, bg, border]`, chip: `font-weight:650; letter-spacing:.02em;
padding:2px 7px; border-radius:5px;` — font-size **10px** (9px in the small
variant used by popover/dependency rows).

| Type | color | bg | border |
|---|---|---|---|
| bug | `#e07a7a` | `rgba(224,108,108,.09)` | `rgba(224,108,108,.28)` |
| improvement | `#4ecdc4` | `rgba(78,205,196,.09)` | `rgba(78,205,196,.28)` |
| epic | `#a78bfa` | `rgba(167,139,250,.09)` | `rgba(167,139,250,.28)` |
| task | `#9ba1ab` | `#22252b` | `#2c2f36` |

## Priority (`PRIO`) — three ascending bars

Bars: widths `3px`, heights `5/8/11px`, `border-radius:1px`, `gap:1.5px`,
bottom-aligned. Lit bars use the priority color; unlit bars `#2c2f36`.
`none` renders **nothing** (not gray bars).

| Priority | color | bars lit |
|---|---|---|
| urgent | `#ef6b6b` | 3 |
| high | `#e29a5a` | 3 |
| medium | `#e2c95a` | 2 |
| low | `#6b93c4` | 1 |

## Node kinds (`KIND_ICON`)

Mono glyph + color: function `ƒ #3ecf72` · file `≣ #9ba1ab` · class
`◇ #6b93c4` · call `↦ #8b919d` · folder `▸ #8b919d`.

## Columns (`COLUMNS`) — dots

backlog `#5c6270` · todo `#6b93c4` · inprogress `#3ecf72` ·
inreview `#e2a03f` · done `#4ea877`.

## Misc chips

- **Label chip**: `#9ba1ab` on `#22252b`, border `#2c2f36`, radius 99px —
  10px/2px-7px on cards, 10.5px/3px-9px in the detail panel.
- **Blocked pill**: `⊘ blocked`, `#e07a7a` on `rgba(224,108,108,.08)`,
  border `rgba(224,108,108,.25)`, 10px, 600.
- **Shared chip**: `⑂ shared`, `#a78bfa` on `rgba(167,139,250,.09)`,
  border `rgba(167,139,250,.28)`, 9.5px, 600.
- **Hot chip** (anchors): `hot · n tasks`, `amber.text` on `amber.bg`,
  border `rgba(226,160,63,.3)`, 9.5px, 650, radius 99px.

## Typography & shape

- UI font: `system-ui, -apple-system, 'Segoe UI', sans-serif`. Mono:
  `'JetBrains Mono', monospace` (weights 400/500/600 loaded).
- **Mono is semantic**: task keys `VN-n` (10–10.5px), counts, qnames (10px
  chips / 12px panel rows), statuses in rows (9.5px), timestamps (9.5–10px),
  the anchored-node filter input. Never mono for titles or prose.
- Radii: cards/nodes `10px` · columns `11px` · inputs/fields `8px` ·
  section lists/description `9px` · chips `99px` (pill) or `5px` (type) ·
  small buttons `6–7px`.
- Scrollbars: 10px, thumb `#2b2e34` with `#17181b` border, radius 6px.
- Placeholders: `#5c6270`. Focus outlines: none — focus is always a border
  color change (`green.core`).

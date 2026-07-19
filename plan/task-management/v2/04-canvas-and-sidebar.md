# v2 · 04 — Canvas badge & popover · Sidebar badges · Tab count

Mock regions: `Canvas`, `Canvas node`, `Node task popover`, `Sidebar`, and
the top tab bar. These decorate existing surfaces — no new screens.

## Canvas node — task badge

In the node header, after the node name (mock places it between name and
the ▾ button): a pill button, mono 10px/650, padding `1px 8px`,
radius 99px:

- **1 open task** → green: `#8fd4a8` on `rgba(62,207,114,.08)`, border
  `rgba(62,207,114,.25)`. Tooltip `1 open task`.
- **hot (≥2)** → amber: `#e2b95a` on `rgba(226,160,63,.12)`, border
  `rgba(226,160,63,.4)`. Tooltip `Hot node — {n} open tasks converge here`.
- zero → nothing rendered.

Counts come from the anchor-summary query keyed by node id (v1 mechanism,
unchanged). Hover `filter:brightness(1.15)`. Click **stops propagation**
and toggles the popover (below) — it must not select the node or start a
React Flow drag (`nodrag`/`nopan` care, as the header buttons already do).

## Canvas node — hot & focused treatments

- **Hot**: border `rgba(226,160,63,.5)` + `hotGlow` animation (01), 2.6s
  infinite. Under `prefers-reduced-motion`: static amber border, no
  animation. (Mock exposes a `hotGlow` prop toggle — keep the CSS gated so
  turning it off is one flag.)
- **Focused** (jump target from anchor chips / Show on canvas): border
  `rgba(62,207,114,.6)` + ring `0 0 0 3px rgba(62,207,114,.15)` over the
  normal shadow.
- Hot beats focused when both apply (mock's ternary order).

## Node task popover — read-only in v2

Anchored under the node (mock: `top:calc(100% + 8px); left:0`), width
264px, `bg #1d1f24`, border `#2c2f36`, radius 11px,
`box-shadow:0 16px 48px rgba(0,0,0,.55)`, padding 5px, `z-index` above
nodes.

- **Header**: `OPEN TASKS · {node name}` — 10px/700/`.08em` `#6b7280`;
  when hot, suffix `● hot node` in `#e2a03f` (600, normal tracking).
- **Task rows** (one per open task anchored to the node, through the
  closure — same set the badge counts): full-width buttons, padding
  `8px 9px`, radius 8px, hover bg `#26292f`: small type chip (9px, 01) ·
  title 12px/550 `#e6e8ec` ellipsized · status mono 9.5px `#8b919d`
  right-aligned. Click → close popover + open the detail panel.
- **Dismiss**: a full-canvas transparent overlay behind the popover closes
  it on click (mock's `popoverAny` layer); Esc too. Only one popover open
  at a time.

The v1-plan extras (link toggles, `＋ Attach task…` row, drag-transfer)
are **not in the mock** and not in v2 — the popover is a list. Linking
lives in the New-task modal and the detail panel (`../fixes/03`).

## Sidebar tree — count badges

On tree rows (existing `TreeNode`): right-aligned pill, mono 9.5px/600,
padding `1px 6px`, radius 99px — green variant (`#8fd4a8` /
`rgba(62,207,114,.07)` / `rgba(62,207,114,.2)`) for 1 task, amber variant
(`#e2b95a` / `rgba(226,160,63,.1)` / `rgba(226,160,63,.35)`) for hot.
Zero = no chip. Counts are exact-node from the anchor-summary map
(v1 shipped this — restyle to these tokens).

## Top tab bar — Tasks count

The `Tasks` workspace tab trigger carries the open-task count as a chip
(mock: `margin-left:6px`, mono 10px, `#8b919d` on `#22252b`, border
`#2c2f36`, padding `1px 6px`, radius 99px) — a styled chip, not the plain
` 6` text v1 appended. Count = open tasks on the board (not scope-aware in
v2). Hidden at zero.

## Explicitly not in v2

Blockers sidebar section, task lens (and its floating bar), drag-transfer
from popover rows, `Attach task` context action — all absent from the
mock. They stay specced in the v1 plan (05) and `../fixes/05` as
post-fidelity work; nothing in this doc blocks them.

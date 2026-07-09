# 10 — Monaco line highlighter with a line-anchored popover

## What this builds

Today (fix 07) the step popover is a `NodeToolbar` glued to the **node's left edge**.
That is right for **intro steps**. For **block steps** it is one level too coarse:
the explanation should sit next to **the highlighted lines inside the Monaco
editor**, move with editor scroll, canvas pan/zoom, and node position — and stay
readable (unscaled) at any zoom. Plus a stronger in-editor spotlight than the current
line decorations.

This is based on the earlier experiment (PR #47, `useWalkthroughMonaco`) — the
architecture there is correct and we keep its three ideas:

1. **Decorations** for line highlight styling (Monaco-native).
2. **Synced DOM elements inside the editor** for the spotlight band and an invisible
   **anchor element** placed over the popover's target line — positioned from
   `getTopForLineNumber(line) − getScrollTop()` and `getLayoutInfo().contentLeft/Width`,
   re-synced on `onDidScrollChange` / `onDidLayoutChange`.
3. **A layout-epoch counter in the store** — the anchor moves for many reasons
   (editor scroll, canvas pan/zoom, node drag); instead of the popover polling, every
   mover bumps `anchorEpoch`, and the popover layer re-measures the anchor's
   `getBoundingClientRect()` (screen space, so the canvas transform is already baked
   in). Event-driven, rAF-throttled — no useEffect polling loops.

## How it fits what already exists (adapt, don't duplicate)

| Existing | Becomes |
|---|---|
| `useWalkthroughMonacoHighlight.ts` (decorations + dim + reveal) | **Replaced** by the new `useWalkthroughMonaco.ts` (decorations + spotlight + anchor + reveal). Delete the old hook when done — two hooks fighting over `deltaDecorations` is a bug factory. |
| Fix-07 `NodeToolbar` + `StepPopover` on the node | **Kept for intro steps only.** Block steps hide the NodeToolbar and show the new line-anchored popover. Same `StepPopover` content component in both — one source of truth for text/Prev/Next/⚠. |
| Store `highlight: {nodeId, startLine, endLine}` | Kept as-is — the new hook consumes it (build a one-element `lines` array internally; multi-range stays possible later without another rewrite). |
| Line mapping (`absoluteToEditorLine`, clamp) | Kept — the store carries **absolute** file lines; the hook converts once, exactly like the old hook did. Do not lose this: the experiment code assumed editor-local lines. |

## The anchor decision (which popover shows when)

Pure derivation from the current step — **no new state**:

```ts
// store/selectors.ts (new small file)
export type StepAnchor =
  | { type: "node"; nodeId: string }
  | { type: "code-line"; nodeId: string; line: number };  // absolute file line

export function currentStepAnchor(s: WalkthroughState): StepAnchor | null {
  if (s.phase !== "playing" || s.cursor < 0) return null;
  const step = s.playerSteps[s.cursor];
  if (!step) return null;
  const hl = step.actions.find((a) => a.type === "highlight_lines");
  return hl
    ? { type: "code-line", nodeId: step.nodeId, line: hl.startLine }
    : { type: "node", nodeId: step.nodeId };
}
```

- `EnhancedNode`'s NodeToolbar visibility changes from "is current step's node" to
  "current anchor is `node` type AND mine".
- The new PopoverLayer renders only when the anchor is `code-line`.

New store field: `anchorEpoch: number` + action `bumpAnchorEpoch()` (rAF-throttled at
the call sites, as in the experiment).

## Piece 1 — `hooks/useWalkthroughMonaco.ts`

Start from the experiment's code (pasted in the PR / user message) and make these
changes — otherwise keep its structure, including the cleanup discipline:

1. **Inputs:** `(nodeId: string, nodeStartLine: number | undefined, showDiff: boolean, codeLoaded: boolean)`.
   Returns `{ onMount }` like the experiment (NodeCodeView passes it to `CodeEditor`).
2. **Consume the current store**, not the experiment's:
   - highlight source: `useWalkthroughStore((s) => s.highlight?.nodeId === nodeId ? s.highlight : null)`;
   - anchor source: `currentStepAnchor` selector above;
   - epoch bump: `bumpAnchorEpoch` (replaces `bumpCodeAnchorLayoutEpoch`).
3. **Convert absolute → editor lines** with the existing `lineMapping.ts` before any
   Monaco call (`from = absoluteToEditorLine(highlight.startLine, nodeStartLine)`,
   clamp with `clampEditorRange`). The anchor's `data-line` keeps the **absolute**
   line (that is what the layer/tests reason about); the pixel math uses editor lines.
4. Keep the decoration effect (`walkthrough-monaco-line-deco`, whole-line, clamped)
   and keep the current dim behavior: **also** decorate out-of-range lines with the
   existing `.walkthrough-dim` class (the experiment dropped dimming; we keep it —
   it is the in-editor spotlight's other half).
5. Keep the reveal effect (`revealLineInCenter` on the first highlighted line), but
   gate everything on `codeLoaded` — the current hook's readiness lesson (Monaco
   mounts before code arrives; effects must re-run when `codeLoaded` flips).
6. Keep the spotlight + anchor element effect verbatim in spirit:
   - both elements `position: absolute`, `pointer-events: none`, appended to
     `editor.getDomNode()`;
   - `sync()` positions both from `getTopForLineNumber`/`getScrollTop`/`getLayoutInfo`;
   - listeners: `onDidScrollChange`, `onDidLayoutChange`, plus initial `sync()`;
   - every `sync()` ends with the rAF-throttled `bumpAnchorEpoch()` **only when**
     the visible anchor is this node's (the experiment's guard — keep it);
   - cleanup disposes listeners, cancels the pending rAF, removes both elements.
7. **Do not** keep the experiment's `highlights: Map` / `popoverVisible` /
   `popover.anchor` store shape — that store never landed; ours is the one in
   `useWalkthroughStore.ts`.

## Piece 2 — `components/CodeLinePopoverLayer.tsx`

A single screen-space layer, portaled to `document.body`, that positions the shared
`StepPopover` next to the anchor element:

```
subscribe: anchor (currentStepAnchor), anchorEpoch, phase
if anchor?.type !== "code-line" → render null
measure: document.querySelector(
  `[data-walkthrough-code-anchor][data-node-id="${anchor.nodeId}"]`
)?.getBoundingClientRect()
if no rect or rect.width === 0 → render null (editor not open yet; the
  node_intro NodeToolbar already covered the intro beat)
position (manual, no new deps):
  preferred: left of the editor content box —
    x = rect.left − POPOVER_W − 12, y = rect.top + rect.height/2 − POPOVER_H/2
  flip right when x < 8: x = rect.right + 12
  clamp y into [8, innerHeight − POPOVER_H − 8]
  ("always visible": when the rect is fully off-screen, clamp to the nearest
   viewport edge instead of hiding — the popover is the tour's thread)
render: fixed-position div, width ~360 px, z-index above canvas below dialogs
  (reuse the overlay z-scale from WalkthroughStepOverlay), containing <StepPopover/>
  with stopPropagation guards (same as fix 07 Step A)
```

Measurement happens in the render path keyed by `anchorEpoch` (a `useMemo` on
`[anchor, anchorEpoch]`) — **not** in an effect loop. The rect only changes when
someone bumped the epoch, and everyone who moves the anchor bumps it:

| Mover | Who bumps |
|---|---|
| Editor scroll / layout | the hook's `sync()` (Piece 1) |
| Canvas pan / zoom | `CanvasView`: in the existing `onMove`-family handlers add a rAF-throttled `bumpAnchorEpoch()` while `phase === "playing"` (add `onMove` prop next to the existing `onMoveStart`) |
| Node drag | covered by canvas `onMove`? **No** — node drag fires `onNodeDrag`; add the same throttled bump there |
| Window resize | one `resize` listener inside the layer (`useEffect` with cleanup — a listener, not a loop) |
| Step change | `cursor` change already re-renders the layer via the anchor selector |

Mount the layer once in `WalkthroughStepOverlay` (beside the pill + executor mount).

## Piece 3 — visibility switch for the NodeToolbar popover

In `EnhancedNode.tsx`, replace the fix-07 visibility with the anchor selector:

```ts
const anchor = useWalkthroughStore(currentStepAnchor);       // memoized selector
const isNodePopover = anchor?.type === "node" && anchor.nodeId === (data.nodeId ?? "");
```

`NodeToolbar isVisible={isNodePopover}`. The ring class
(`walkthrough-current-node`) keeps its old condition (current step's node,
regardless of anchor type). Careful with selector identity: `currentStepAnchor`
returns a new object per call — subscribe with a comparator or select the two
primitive fields (`type`, `nodeId`) separately to avoid re-render storms.

## Piece 4 — CSS (`src/index.css`)

Keep the existing `.walkthrough-line` (used by decorations — rename usages if you
adopt `walkthrough-monaco-line-deco`, do NOT keep both names) and `.walkthrough-dim`.
Add:

```css
.walkthrough-monaco-spotlight {
  position: absolute;
  pointer-events: none;
  background: color-mix(in oklch, var(--primary) 10%, transparent);
  outline: 1px solid color-mix(in oklch, var(--primary) 45%, transparent);
  border-radius: 4px;
  transition: top 0.15s ease, height 0.15s ease;
  z-index: 5; /* above Monaco text layers' backgrounds, below its widgets */
}
```

Verify the z-index against a real editor (Monaco layers: margin, lines, minimap are
off) — adjust so text stays readable THROUGH the band (background tint, not cover).

## Mock data — how to feed this thing

> ⚠ **SUPERSEDED by [11-backend-only-mock.md](11-backend-only-mock.md)** (2026-07-09):
> the frontend mock generator and `mockOverrides.ts` are deleted; block data comes
> from the backend fake pipeline over real code. The rest of this doc (hook, layer,
> anchors, CSS) is unaffected. Section kept for history only.

Two levels, both already mostly wired:

1. **Free (after fix 01):** the mock generator builds blocks from the **real**
   selected node's line range, so every gated function you tour exercises
   decorations, spotlight, anchor, and popover with zero extra work. This is the
   default demo path.
2. **Hand-tuned scenarios — add `source/mockOverrides.ts`:**

```ts
// Keyed by node NAME (or qname). Checked by the mock generator BEFORE random splitting.
export const MOCK_BLOCK_OVERRIDES: Record<string, {
  blocks: { start_line: number; end_line: number; focus: string; text: string }[];
}> = {
  // example — tune to a node that exists in YOUR project:
  charge: {
    blocks: [
      { start_line: 12, end_line: 18, focus: "validate the card",
        text: "Input is checked first so bad cards fail before any network call." },
      { start_line: 19, end_line: 31, focus: "provider call",
        text: "The provider client is invoked with an idempotency key." },
    ],
  },
};
```

   In `mockGenerator.ts`, where blocks are produced for a gated stop: if
   `MOCK_BLOCK_OVERRIDES[node.name]` exists, use those blocks **verbatim** (clamped
   to the node's real `[start_line, end_line]`; log a warning if a range falls
   outside instead of silently clamping — that means the override is stale).
   This gives a stable, repeatable scene for tuning popover placement, long-text
   wrapping, first/last-line anchors, and one-line blocks — without touching the
   random path everyone else uses.

3. **Edge fixtures worth adding to the overrides while testing:** a block at the
   function's **first** line (popover must not cover the node header), a block at
   the **last** line (y-clamp), a one-line block (spotlight height = 1 line), and a
   text of ~500 chars (card growth + clamp).

## Prove it

1. Tour a gated function (mock): block steps show the spotlight band over the exact
   lines, the popover floats left of the editor content at the first block line, and
   the NodeToolbar popover is hidden; intro steps show the reverse.
2. Scroll **inside** Monaco during a block step: band and popover track the line;
   popover clamps to the viewport edge when the line scrolls out (never vanishes).
3. Pan/zoom the canvas: popover follows (epoch bump from `onMove`), text stays
   unscaled; drag the node — same.
4. Prev/Next across blocks of one node: no flicker, decorations replaced not
   stacked (watch decoration count via
   `editor.getModel().getAllDecorations().length` in devtools while stepping).
5. Exit mid-block: band, anchor, popover, decorations all gone; no listeners leaked
   (Performance tab: no recurring rAF).
6. Override scenario from `mockOverrides.ts` renders exactly the authored ranges and
   texts; the four edge fixtures behave (first/last line, one-liner, long text).
7. `yarn test` green — add unit tests for `currentStepAnchor` (block step → code-line
   with the block's start line; intro → node; not playing → null).

# 07 — Step popover anchored to the node (left side), tracking, always on top

## The problem

The step text lives in a card fixed at the **bottom of the screen**
(`WalkthroughStepOverlay` → `StepCard`). The user looks at the node being explained
and the words are somewhere else; on a busy canvas it is hard to tell which node the
step is even about. Wanted: the popover sits **at the node, on its left side**, moves
with the node when the canvas pans/zooms, and renders **above** all other nodes and
edges.

## The right tool: ReactFlow's `NodeToolbar`

`@xyflow/react` v12 ships a `NodeToolbar` component built for exactly this:

- rendered inside a node component, but portaled to a layer **above** the canvas
  content (covers other nodes — the "overlay should cover others" requirement);
- automatically **tracks the node** through pan/zoom/drag;
- does **not scale** with zoom (stays readable at any zoom level);
- `position={Position.Left}` puts it on the left side, `align` controls centering;
- `isVisible` prop controls it explicitly (independent of node selection).

Before coding, verify it exists in the installed version: open
`src/frontend/node_modules/@xyflow/react/dist/esm/index.d.ts` and search for
`NodeToolbar`. Read its props type (`NodeToolbarProps`): you need `isVisible`,
`position`, `align`, `offset`. Do not guess prop names.

## Files

| File | Action |
|---|---|
| `walkthrough/components/StepPopover.tsx` | NEW — the popover content (reuses StepCard's internals) |
| `Canvas/components/nodes/EnhancedNode.tsx` | Mount `<NodeToolbar>` with `StepPopover` |
| `walkthrough/components/StepCard.tsx` | Slim down: it becomes the fallback / progress bar (see below) |
| `walkthrough/components/WalkthroughStepOverlay.tsx` | Keep executor mount + slim progress pill only |

## Step A — `StepPopover.tsx`

Extract the inner content of `StepCard` (title row with ⚠ + counter, text/shimmer
body, Exit/Prev/Next row) into a presentational component `StepPopover` that takes no
props and reads the store itself (same selectors StepCard uses today). Constraints:

- Width: `w-[360px] max-w-[70vw]`. The card look (border, bg-background, shadow-lg,
  rounded-xl) moves here.
- It must **stop event propagation** for clicks/wheel (`onClick`,
  `onPointerDown`, `onWheel` → `e.stopPropagation()`) so pressing Next doesn't
  select/drag the node underneath or zoom the canvas.
- Add `data-walkthrough-popover` attribute — used by tests and by the keyboard guard
  check below.

## Step B — mount in `EnhancedNode.tsx`

EnhancedNode already knows its `data.nodeId`. Add, near the root of its JSX:

```tsx
const isCurrentStepNode = useWalkthroughStore(
  (s) =>
    s.phase === "playing" &&
    s.playerSteps[s.cursor]?.nodeId === (data.nodeId ?? ""),
);
...
<NodeToolbar
  isVisible={isCurrentStepNode}
  position={Position.Left}
  align="center"
  offset={16}
>
  <StepPopover />
</NodeToolbar>
```

Rules:

- The zustand selector returns a **boolean** (not an object), so only the two nodes
  whose visibility flips re-render on a step change. Do not select the whole step
  object here.
- Import `NodeToolbar`, `Position` from `@xyflow/react`.
- Exactly one node can match at a time (one cursor), so exactly one popover exists.
- While you are in this file: add the **current-step ring** — when
  `isCurrentStepNode`, add a class to the node wrapper (e.g.
  `walkthrough-current-node`) and define it in `src/index.css` next to the existing
  walkthrough classes: a 2px accent outline + a soft pulse (see the keyframes sketch
  in `plan/cognitive-replay/05-canvas-integration.md`, "focus-ring"). This answers
  "hard to tell where it is" together with fix 08's camera rules.

## Step C — what remains at the bottom

Replace the bottom `StepCard` usage inside `WalkthroughStepOverlay` with a slim
**progress pill** (new tiny component or a trimmed StepCard): step counter
(`7 / 21`), tour title, and an Exit button — one row, `h-10`, centered, no text body.
The full text + Prev/Next live in the node popover now. Keep `useStepExecutor()`
mounted in the overlay exactly as before (it must run whenever a session exists —
verify the early-return order: hooks first).

Why keep anything at the bottom: when the current node is off-viewport for a moment
(user panned away), the pill is the constant anchor showing the tour is alive.

## Step D — keyboard and focus

`useWalkthroughKeyboard` guards `input/textarea/contentEditable`. Buttons inside the
popover are none of those, so Arrow keys keep working even after clicking Next (the
button keeps focus — arrows don't trigger buttons). Verify Escape still exits when
focus is inside the popover.

## Known limitation (accept it, document it)

If the user pans the current node fully off-screen, the popover (which tracks the
node) goes off-screen with it. That is correct behavior — fix 08 makes the camera
keep the current node in view, and the bottom pill + outline row remain as recovery
paths. Do not add a "detach popover" mode.

## Prove it

1. Play a tour: the popover appears glued to the **left edge** of the current node,
   vertically centered, above all neighboring nodes/edges (drag another node under
   it to check stacking).
2. Pan and zoom: the popover follows the node; its text size does not change with
   zoom.
3. Next/Prev from inside the popover: no node selection flicker, no canvas zoom from
   scrolling inside the popover text.
4. The current node shows the accent ring; only one node at a time.
5. Bottom shows only the slim pill; Exit works from both pill and popover.
6. `yarn test` green; add one vitest for the `isCurrentStepNode` selector logic if
   the store exposes it as a helper (optional).

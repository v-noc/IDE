# 09 — Spotlight, don't re-root: keep every node visible during the tour

## The problem (what the user sees)

During playback the canvas shows **only the current node** — all other nodes vanish.
There is no sense of where the node lives relative to its siblings, and transitions
are meaningless because there is nothing to travel past. Wanted: all tour nodes stay
visible; the current one is zoomed to and **spotlighted**; everything else stays on
screen but **dimmed under an overlay — the driver.js effect**.

## Root cause (verified — read this carefully, it is not obvious)

In this canvas, **primary selection doubles as the layout root**:

- `CanvasView.tsx`: `const centerNode = selectedNode` → passed to
  `useEnhancedTreeLayout` as the traversal start. The layout renders **only the
  subtree of the selected node**.
- The executor (after fix 08) calls
  `useProjectStore.getState().setSelectedNode(tabId, node)` on every `select_node`
  action → every step **re-roots the canvas at the current stop** → for a leaf
  function the canvas is one node.
- `ensureOnCanvas.ts` does the same through a side door: its injection path calls
  `clearFocus` + `pushFocusBulk`, and `focusSlice.pushFocusBulk` **also sets
  `selectedNode`** (open `store/slices/focusSlice.ts` and confirm). So even
  `prepareTour` re-roots repeatedly while preparing.

Historical note for the implementer: fix 08 introduced `setSelectedNode` to avoid
`handleNodeSelection`'s portal-tab side effects. That was half right — the portal
side effects are gone — but it swapped them for the re-rooting side effect. This doc
supersedes that instruction: **playback must not touch primary selection or focus at
all after Play begins.**

## Target behavior

1. At **Play**: root the canvas ONCE at the tour's start node
   (`visit_list.nodes[0]`). Every stop of the tour lives inside that subtree (calls
   are visited as call nodes inside their caller — verify against
   `../03-traversal.md` if in doubt), so one root shows the whole tour.
2. During steps: the current stop is marked with **secondary selection** (the
   canvas's own "highlight without re-rooting" convention — `onNodeClick` in
   `CanvasView` uses `"secondary"` for exactly this) plus the fix-07 ring class.
   Primary selection and the focus stack are never written between steps.
3. All other nodes stay rendered, **dimmed** (driver.js-style spotlight); the camera
   zooms/slides to the current node (fix 08's `moveCameraToStep` stays as is).

## Files

| File | Action |
|---|---|
| `walkthrough/executor/ensureOnCanvas.ts` | Add `reroot` option; injection expands WITHOUT focus writes |
| `walkthrough/executor/prepareTour.ts` | Root once at the start node; stops use `reroot: false` |
| `walkthrough/executor/useStepExecutor.ts` | `setSecondarySelectedNode` instead of `setSelectedNode` |
| `Canvas/components/CanvasView.tsx` | `walkthrough-playing` class on the root div |
| `Canvas/components/nodes/EnhancedNode.tsx` | `walkthrough-node` class always + current class (fix 07) |
| `src/index.css` | The dimming rules |
| `walkthrough/executor/restoreView.ts` | Verify only (it restores primary selection on exit — still correct) |

## Step A — `ensureOnCanvas(queryClient, tabId, nodeId, opts?: { reroot?: boolean })`

- Fast path (node found in tree/descendant cache): return it, **zero store writes**
  (this is already true — verify, don't assume).
- Injection path (lineage fetch needed):
  - When `reroot: false` (default): call
    `useProjectStore.getState().expandNodesBulk(tabId, lineage.map(n => n.id))`
    **only**. No `clearFocus`, no `pushFocusBulk`. Expansion is what makes the
    branch render; focus was only ever needed by the call-portal flow this code was
    copied from.
  - When `reroot: true`: current behavior (clearFocus + pushFocusBulk) — used
    exactly once, at Play, for the tour root.

## Step B — `prepareTour.ts`

1. First: `ensureOnCanvas(queryClient, tabId, visitList.nodes[0].node_id, { reroot: true })`
   — this is THE root change of the whole tour, and it happens before any step.
2. Then loop the remaining stops with `{ reroot: false }` (order unchanged,
   sequential, error handling unchanged).
3. Delete the final "restore focus to root" call — with no re-rooting in the loop,
   there is nothing to restore.
4. `expandNodesBulk` of all stop ids stays.

## Step C — executor selection

In `useStepExecutor.runActions`, replace

```ts
setSelectedNode(tabId, node);
```

with

```ts
useProjectStore.getState().setSecondarySelectedNode(tabId, node);
```

Check `selectionSlice.ts` first: confirm `setSecondarySelectedNode` writes only
`secondarySelectedNode` (no focus, no primary). Side benefit: the right sidebar
follows the tour the same way it follows a plain canvas click. On `exit()`,
`restoreView` already restores `secondarySelectedNode` from the snapshot — verify
the `SavedView` capture includes it (it does — `secondarySelectedNodeId`).

## Step D — the spotlight (CSS dimming, not literal driver.js)

Why not the installed `driver.js` itself: driver.js draws a **screen-space** SVG
overlay with a cutout at a DOM element's bounding rect. Our nodes live inside
ReactFlow's pan/zoom transform, and the tour animates the viewport — the cutout
would desync on every pan/zoom frame and need constant manual refresh. CSS dimming
on the canvas's own elements produces the same spotlight look and moves natively
with the canvas. (Do not import driver.js for this.)

1. `CanvasView.tsx`: subscribe once —
   `const isTourPlaying = useWalkthroughStore((s) => s.phase === "playing");`
   and toggle a class on the existing root div:
   `className={cn("h-full w-full bg-background", isTourPlaying && "walkthrough-playing")}`.
2. `EnhancedNode.tsx`: the outermost element gets `walkthrough-node`
   unconditionally, plus the existing fix-07 `walkthrough-current-node` when it is
   the current stop.
3. `src/index.css`:

```css
/* Walkthrough spotlight: dim everything except the current stop */
.walkthrough-playing .walkthrough-node {
  opacity: 0.3;
  filter: saturate(0.6);
  transition: opacity 0.25s ease, filter 0.25s ease;
}
.walkthrough-playing .walkthrough-node.walkthrough-current-node {
  opacity: 1;
  filter: none;
}
.walkthrough-playing .react-flow__edge {
  opacity: 0.2;
  transition: opacity 0.25s ease;
}
```

Notes:
- Dim the **inner** node element (`walkthrough-node`), not `.react-flow__node`, so
  no `:has()` selector is needed and ReactFlow's own selection/drag styling is
  untouched.
- The fix-07 popover (`NodeToolbar`) renders in a separate portal layer — it is not
  affected by the dimming. Verify visually.
- Keep the values as CSS, not inline styles — designers can tune 0.3/0.6 later.

## Step E — leave the camera alone

`moveCameraToStep` (fix 08) already does the right thing: zoom-1 focus on cursor 0,
zoom-preserving slide otherwise, skip when in view. With re-rooting gone, slides now
have visible context to slide past — which is the point. No changes here.

## Prove it

1. Play a tour on a class at depth 1: after Play, the canvas shows the class **and
   all its methods**; they never disappear during the tour.
2. Current stop is full-color with the ring + popover; every other node is dimmed
   and desaturated; edges faded. The spotlight moves with Next/Prev with a soft
   fade.
3. Watching a transition, you can see the camera slide **past dimmed nodes** — you
   can tell where you came from and where you are.
4. During the tour, the right sidebar shows the current stop's details (secondary
   selection), and NO "Explore" tabs appear.
5. Exit: dimming gone instantly, selection/focus/expansion restored, canvas root
   back to the pre-tour selection.
6. Pan/zoom by hand mid-step: dimming stays consistent (it is in canvas space, not
   screen space) — the driver.js-style overlay does not desync.
7. `yarn test` + `yarn lint` green.

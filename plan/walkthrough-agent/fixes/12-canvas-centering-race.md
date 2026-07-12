# 12 — Canvas bug: selecting a node centers on stale coordinates (empty canvas)

General canvas bug, like fix 06 — not walkthrough-specific, but the walkthrough
made it more visible. Symptom: select a node (sidebar, promote, call portal) → the
viewport flies to a seemingly random spot showing **empty canvas**; you must drag
around or press ReactFlow's fit-view button to find your node.

## Reproduce first

1. Open a project, select node A on the canvas root's subtree.
2. From the sidebar, select a node X deep in another branch.
3. Watch: the camera moves, but usually to empty space; X is elsewhere.
4. Press the fit-view control → everything is actually there, just not where the
   camera went.

## Root cause (verified in `CanvasView.tsx` — two stacked races)

The centering code (search for `lastCenteredTargetIdRef`):

```ts
const centerOnTarget = useEffectEvent(() => {
  ...
  const rfNode = nodes.find((n) => n.id === nodeId);
  if (rfNode && rfNode.measured?.width) {
    if (lastCenteredTargetIdRef.current !== nodeId) {
      reactFlowInstanceRef.current.setCenter(...rfNode.position...);
      lastCenteredTargetIdRef.current = nodeId;   // ← once per node id, forever
    }
  } else {
    requestAnimationFrame(centerOnTarget);        // ← uncapped rAF polling
  }
});
useEffect(() => { if (centerNode) centerOnTarget(); ... }, [centerNode, ...]);
```

**Race 1 — it centers on the OLD layout's coordinates.** Selecting X changes
`centerNode`, which is also the **layout root**: `useEnhancedTreeLayout` recomputes
`initialNodes` as a brand-new dagre layout rooted at X — every node's coordinates
change. But `setNodes(initialNodes)` happens in the `syncDiffOverlay` effect, and
state is only visible on the **next** render. The centering effect runs in the same
effects pass and reads `nodes` — **still the previous layout**. If X was already on
screen (the common case), it is found there **with its old position and old
measured size** → `setCenter(old coordinates)` → the ref records "X centered".
One render later the new layout lands, X actually sits somewhere else entirely, the
viewport points at nothing — and the `lastCenteredTargetIdRef` guard **blocks every
correction attempt from then on**. That is the "random empty spot".

**Race 2 — the layout keeps moving after centering.** Even when the timing works
out, two async reflows follow every selection: the lineage effect
(`getLineage` → `expandNodesBulk`) changes `expandedNodeIds`, and lazy children
arriving (post fix 06) recompute the layout again. Each reflow moves the target's
position; once-per-id centering never follows.

The rAF branch has a third, smaller problem: uncapped self-rescheduling polling —
the pattern we already removed elsewhere (fix 03-F5).

## The fix: follow the target through layout changes (dependency-driven, no rAF)

Delete `lastCenteredTargetIdRef`, the `centerOnTarget` effect-event, and its effect.
Replace with a derived target + one honest effect:

```ts
// 1. Derive the target's committed center from CURRENT nodes state.
//    null until the node exists in the layout AND is measured — so "not there
//    yet" needs no polling: measurement/layout changes update `nodes`, which
//    recomputes this memo, which re-runs the effect.
const centerTarget = useMemo(() => {
  const id = centerNode?.id;
  if (!id) return null;
  const n = nodes.find((node) => node.id === id);
  if (!n?.measured?.width) return null;
  return {
    id,
    x: n.position.x + n.measured.width / 2,
    y: n.position.y + (n.measured.height ?? 0) / 2,
  };
}, [nodes, centerNode?.id]);

// 2. Follow-mode flag: a new selection re-arms following; a USER pan/zoom
//    disarms it (programmatic moves pass no event — the existing
//    `if (!event) return` guard in onMoveStart already distinguishes them,
//    so setCenter's own animation cannot disarm the follow).
const followSelectionRef = useRef(false);
useEffect(() => {
  followSelectionRef.current = true;
}, [centerNode?.id]);
// in onMoveStart, alongside the walkthrough check:
//   if (event) followSelectionRef.current = false;

// 3. Center whenever the target's committed position changes, while following.
useEffect(() => {
  if (!centerTarget || !followSelectionRef.current) return;
  if (useWalkthroughStore.getState().phase === "playing") return;   // keep 08's rule
  reactFlowInstanceRef.current?.setCenter(centerTarget.x, centerTarget.y, {
    zoom: 1,
    duration: 300,
  });
}, [centerTarget?.id, centerTarget?.x, centerTarget?.y]);
```

Why this is correct where the old code raced:

- The effect depends on the target's **position from committed state** — when the
  re-rooted layout lands one render later, the position changes, the effect re-runs,
  the camera corrects. Same for the lineage reflow and lazy-children reflow: every
  shift re-centers, so the camera **follows the layout until it settles**.
- No stale reads: no effect-event peeking at this-render state, no rAF polling —
  "node not measured yet" simply means `centerTarget` is null until ReactFlow's
  dimension pass updates `nodes`.
- The user stays in control: the first real pointer gesture flips
  `followSelectionRef` off, so late reflows (a slow descendants fetch) don't yank
  the camera back after the user started exploring.
- Walkthrough playback keeps its single-camera-driver rule (fix 08/09).

Known accepted quirks (do not "fix" without a report):
- Re-selecting the same node does not re-center (the follow flag re-arms only on id
  change). If dogfooding wants "click selected node again to re-center", re-arm in
  `handleNodeSelection` — one line, later.
- During the few layout settles, the camera may glide 2–3 times (animated
  `setCenter` restarts). That is the honest behavior — it converges on the real
  position; the old code converged on nothing.

## Prove it

1. The reproduce steps above: selecting a deep node from the sidebar lands the
   camera ON the node — first try, no drag, no fit-view button.
2. Select a node whose children are lazy (never loaded): camera lands on it, then
   stays with it as children stream in and the layout reflows around it.
3. Select X, immediately drag the canvas while children are still loading → the
   camera does NOT jump back when the fetch lands (follow disarmed by the gesture).
4. Call-portal flow (click a call node → Explore tab): the new tab centers on the
   target — same code path, should now be reliable.
5. During a walkthrough, selection changes still never move the camera (suppression
   intact); after Exit, sidebar selection centers normally again.
6. React DevTools profiler: no runaway re-renders from the memo (it recomputes on
   `nodes` changes only); Performance tab: zero recurring rAF.
7. `yarn lint` clean — the deleted effect-event and ref leave no unused imports.

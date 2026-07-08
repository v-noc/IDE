# 06 — Canvas bug: expanded node's lazy children don't appear until collapse + re-expand

This is a **general canvas bug**, not walkthrough-specific — the walkthrough just
trips over it constantly (it expands nodes programmatically). Fix it in the canvas;
do NOT work around it in the walkthrough.

## Reproduce first (so you know when it's fixed)

1. Open a project. Find a node whose children were never loaded (fresh node, not
   opened via the sidebar — it has `lazy_child_ids` but no `children`).
2. Click its expand toggle on the canvas.
3. Watch the network tab: the `/descendants` request fires. The canvas shows **no
   children**.
4. Collapse, expand again → children appear (they were in the react-query cache by
   then).

## Root cause (verified in code, two layers)

**Layer 1 — the missing dependency.** In
`src/frontend/src/features/Dashboard/features/Main/components/Canvas/hooks/useEnhancedTreeLayout.tsx`,
the big layout `useMemo` (builds `initialNodes`/`initialEdges`, runs dagre) **reads**
`lazyChildrenByParentId` inside (search for
`lazyChildrenByParentId?.get(nodeId)`), but its dependency array is:

```ts
}, [centerNode, expandedNodeIds, metadataMap]);
```

`lazyChildrenByParentId` is not there (there is an
`eslint-disable-next-line react-hooks/exhaustive-deps` hiding the warning). Timeline
of the bug: expand → `expandedNodeIds` changes → memo recomputes **while the fetch is
still in flight** (map is empty for that parent) → fetch resolves → map changes → memo
**does not recompute** → stale layout until the next `expandedNodeIds` change
(= collapse/expand).

**Layer 2 — why you can't just add the dep.** In `CanvasView.tsx`,
`lazyChildrenByParentId` is built by a `useMemo` whose deps are
`[lazyParentIds, descendantQueries]` — and `descendantQueries` is the raw array from
`useQueries`, which is a **new array reference on every render** (react-query v5).
Adding the map to the layout deps as-is would make dagre re-run on every render —
layout churn, the opposite problem. The map needs a **stable identity that only
changes when actual data changes** first.

## The fix (no new useEffect — this is a pure memoization fix)

### Step 1 — stabilize the map in `CanvasView.tsx`

Replace the `lazyChildrenByParentId` memo's dependency on the raw query array with a
key derived from the queries' data timestamps:

```ts
const descendantsDataKey = descendantQueries
  .map((q) => q.dataUpdatedAt)
  .join("|");

const lazyChildrenByParentId = useMemo(() => {
  const m = new Map<string, AnyNodeTree[]>();
  lazyParentIds.forEach((parentId, i) => {
    const roots = descendantQueries[i]?.data?.children;
    if (roots?.length) m.set(parentId, roots as unknown as AnyNodeTree[]);
  });
  return m;
  // descendantsDataKey is the change signal for descendantQueries' DATA;
  // the array identity itself changes every render and must not be a dep.
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, [lazyParentIds, descendantsDataKey]);
```

`dataUpdatedAt` is `0` until a query first resolves and bumps on every refetch — so
the key changes exactly when any parent's children data changes, and never otherwise.

(Alternative considered: `useQueries`' `combine` option, which react-query memoizes.
It also works, but the `dataUpdatedAt` key is simpler to verify and keeps the current
code shape. Pick ONE — do not do both.)

### Step 2 — add the dep in `useEnhancedTreeLayout.tsx`

Add `lazyChildrenByParentId` to the layout memo's dependency array:

```ts
}, [centerNode, expandedNodeIds, metadataMap, lazyChildrenByParentId]);
```

Keep `toggleNodeExpansion` OUT (the existing comment about it stays — it's a stable
store action captured per-node in `onToggle`; including it would be pointless churn).
Remove the now-stale part of the eslint-disable comment if the linter allows, or
update the comment to name exactly what is excluded and why.

### Step 3 — remove the debug log

Same memo starts with `console.log("lazyChildrenByParentId", ...)` — delete it.

## Why this is the right fix and not an effect

The layout is a **pure derivation** of (tree data + expansion state + lazy children).
Derivations belong in `useMemo` with honest deps. An alternative "fix" — a
`useEffect` that watches query completion and forces a re-render or re-toggles
expansion — would paper over the missing dep with more moving parts and re-introduce
the same class of bug next time someone adds an input. (The user explicitly asked:
no useEffect abuse. This fix adds zero effects.)

## Ripple check (do these, they're quick)

- `syncDiffOverlay` in `CanvasView` copies `initialNodes/initialEdges` into
  `useNodesState` via an effect — that effect's deps are `[initialNodes,
  initialEdges]`, so the new recompute flows through automatically. Verify by reading
  it; touch nothing.
- The sidebar uses the same descendants cache; nothing there reads
  `lazyChildrenByParentId`. No change.
- Walkthrough `ensureOnCanvas` + `expandNodesBulk` path: after this fix, a node
  injected and expanded by the tour shows its children as soon as the fetch lands —
  this is what fix 08 (expand-upfront) relies on.

## Prove it

1. The reproduce steps above now show children on the FIRST expand, as soon as the
   request resolves (no collapse/re-expand).
2. Pan/zoom the canvas while a fetch is in flight — no layout jumps on every frame
   (Layer-2 guard works: React DevTools profiler shows the layout memo does not run
   on plain re-renders).
3. Expand three lazy nodes quickly in a row — each one's children appear
   independently as their queries land.
4. `yarn test` and `yarn lint` still green.

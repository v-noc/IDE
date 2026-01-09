# Step 7: Canvas Performance Optimizations

## Goal
Make the Canvas fast with 50+ nodes by adding memoization and lazy loading.

---

## 7a: Memoize Node Types

Move node type registration outside component:

### In `CanvasView.tsx`

```diff
+ // Define OUTSIDE component - stable reference
+ const nodeTypes = {
+   enhanced: EnhancedNode,
+ } as const;

const CanvasView: React.FC<CanvasViewProps> = ({ projectId }) => {
-   const nodeTypes = useMemo(() => ({ enhanced: EnhancedNode }), []);
+   // Use the stable reference defined above

  return (
    <ReactFlow
      nodeTypes={nodeTypes}
      // ...
    />
  );
};
```

---

## 7b: Remove Console.log

```diff
// In CanvasView.tsx
React.useEffect(() => {
  setNodes(initialNodes);
  setEdges(initialEdges);
- console.log(initialEdges);
}, [initialNodes, initialEdges, setNodes, setEdges]);
```

---

## 7c: Lazy Load Monaco Editor

The Monaco code editor is heavy. Load it only when needed:

### In `NodeCodeView.tsx`

```typescript
import { lazy, Suspense } from 'react';

// Lazy load Monaco
const CodeEditor = lazy(() => import('@/components/CodeEditor'));

function CodeEditorSkeleton() {
  return (
    <div className="h-[300px] bg-slate-100 animate-pulse flex items-center justify-center">
      <span className="text-slate-400">Loading editor...</span>
    </div>
  );
}

export function NodeCodeView({ code, onChange, ... }) {
  return (
    <div className="h-[300px] overflow-hidden nodrag">
      <Suspense fallback={<CodeEditorSkeleton />}>
        <CodeEditor
          value={code}
          onChange={onChange}
          // ...
        />
      </Suspense>
    </div>
  );
}
```

---

## 7d: Use Selectors for Store Access

### In `CanvasView.tsx`

```diff
// ❌ Before: Subscribes to entire store
- const { selectedNode, expandedNodeIds, toggleNodeExpansion, projectData } = useProjectStore();

// ✅ After: Only subscribes to what's needed
+ const selectedNode = useProjectStore((s) => s.selectedNode);
+ const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
+ const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
+ const projectData = useProjectStore((s) => s.projectData);
```

---

## 7e: Memoize Layout Calculation

### In `useEnhancedTreeLayout.tsx`

Make sure the layout only recalculates when inputs change:

```typescript
export function useEnhancedTreeLayout({
  centerNode,
  expandedNodeIds,
  toggleNodeExpansion,
  layoutConfig,
}: UseEnhancedTreeLayoutProps) {
  // ✅ useMemo prevents recalculation on parent re-renders
  const { initialNodes, initialEdges } = useMemo(() => {
    if (!centerNode) {
      return { initialNodes: [], initialEdges: [] };
    }
    
    return buildLayout(centerNode, expandedNodeIds, layoutConfig);
  }, [centerNode, expandedNodeIds, layoutConfig]);

  // ... rest
}
```

---

## 7f: Wrap EnhancedNode with memo

Already done in Step 6, but ensure the comparison is good:

```typescript
const EnhancedNode = memo(function EnhancedNode({ data }) {
  // ...
}, (prev, next) => {
  // Custom comparison to reduce re-renders
  return (
    prev.data.nodeId === next.data.nodeId &&
    prev.data.name === next.data.name &&
    prev.data.expanded === next.data.expanded
  );
});
```

---

## Verification

- [ ] Canvas is responsive with many nodes
- [ ] Opening code doesn't lag
- [ ] React DevTools Profiler shows fewer re-renders

---

## Next Step

👉 [Step 8: Split Project Store](./step-08-project-store-slices.md)

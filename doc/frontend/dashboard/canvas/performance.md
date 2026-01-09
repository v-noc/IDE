# Canvas Performance & Scalability

## 🎯 Goal

Handle **100+ nodes** smoothly without lag or excessive re-renders.

---

## ⚠️ Current Performance Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Re-renders on any state change | Not using `memo` properly | Memoize node components |
| All nodes re-render on selection | Selection in parent state | Use selectors |
| Heavy code editor in every node | Monaco is heavy | Lazy load on expand |
| Layout recalculated every render | useEnhancedTreeLayout | useMemo + deps |

---

## ✅ Performance Optimizations

### 1. Memoize Node Components

```typescript
// components/nodes/CanvasNode.tsx
import { memo } from 'react';
import { areEqual } from 'react-window'; // or custom comparison

interface CanvasNodeProps {
  data: EnhancedNodeData;
  selected?: boolean;
}

// ✅ Only re-render when data actually changes
export const CanvasNode = memo(function CanvasNode({
  data,
  selected,
}: CanvasNodeProps) {
  return (
    <div className={`canvas-node ${selected ? 'selected' : ''}`}>
      {/* Node content */}
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison - only re-render if these change
  return (
    prevProps.data.nodeId === nextProps.data.nodeId &&
    prevProps.data.name === nextProps.data.name &&
    prevProps.data.expanded === nextProps.data.expanded &&
    prevProps.data.metadata?.code === nextProps.data.metadata?.code &&
    prevProps.selected === nextProps.selected
  );
});
```

### 2. Lazy Load Code Editor

```typescript
// components/nodes/NodeCodeSection.tsx
import { lazy, Suspense, useState } from 'react';

// ✅ Code editor only loads when needed
const CodeEditor = lazy(() => import('@/components/CodeEditor'));

export function NodeCodeSection({ 
  nodeId,
  onToggle 
}: { 
  nodeId: string;
  onToggle: () => void;
}) {
  const [showCode, setShowCode] = useState(false);
  
  if (!showCode) {
    return (
      <button onClick={() => setShowCode(true)}>
        Show Code
      </button>
    );
  }
  
  return (
    <Suspense fallback={<CodeSkeleton />}>
      <CodeEditor nodeId={nodeId} />
    </Suspense>
  );
}
```

### 3. Virtualize Large Node Lists

For very large graphs, consider virtualizing the node list:

```typescript
// hooks/useVirtualizedNodes.ts
import { useMemo } from 'react';

export function useVirtualizedNodes(
  nodes: Node[],
  viewportBounds: { x: number; y: number; width: number; height: number }
) {
  return useMemo(() => {
    // Only render nodes within viewport + buffer
    const buffer = 200; // pixels
    
    return nodes.filter(node => {
      const { x, y } = node.position;
      const width = node.measured?.width ?? 400;
      const height = node.measured?.height ?? 200;
      
      return (
        x + width > viewportBounds.x - buffer &&
        x < viewportBounds.x + viewportBounds.width + buffer &&
        y + height > viewportBounds.y - buffer &&
        y < viewportBounds.y + viewportBounds.height + buffer
      );
    });
  }, [nodes, viewportBounds]);
}
```

### 4. Optimize Layout Hook

```typescript
// hooks/useCanvasLayout.ts
import { useMemo } from 'react';
import dagre from 'dagre';

export function useCanvasLayout(
  treeData: SimpleTreeNode | null,
  expandedIds: string[],
  config: LayoutConfig
) {
  // ✅ useMemo prevents recalculation on every render
  const { nodes, edges } = useMemo(() => {
    if (!treeData) return { nodes: [], edges: [] };
    
    const graph = new dagre.graphlib.Graph();
    graph.setGraph({ 
      rankdir: 'LR',
      ranksep: config.LEVEL_SPACING_X,
      nodesep: config.SPACING_Y,
    });
    graph.setDefaultEdgeLabel(() => ({}));
    
    // Build graph...
    const nodes = buildNodes(treeData, expandedIds, graph);
    const edges = buildEdges(treeData, expandedIds);
    
    dagre.layout(graph);
    
    // Apply positions
    return {
      nodes: nodes.map(node => ({
        ...node,
        position: {
          x: graph.node(node.id).x,
          y: graph.node(node.id).y,
        },
      })),
      edges,
    };
  }, [treeData, expandedIds, config]); // Only recalculate when these change
  
  return { nodes, edges };
}
```

### 5. Use Selectors for State

```typescript
// ❌ BAD: All nodes re-render when anything in store changes
const CanvasView = () => {
  const store = useProjectStore(); // Subscribes to EVERYTHING
};

// ✅ GOOD: Only re-render when specific values change
const CanvasView = () => {
  const selectedNodeId = useProjectStore((s) => s.selectedNode?._key);
  const expandedIds = useProjectStore((s) => s.expandedNodeIds);
  // Only re-renders when selectedNodeId or expandedIds change
};
```

### 6. Debounce Expensive Operations

```typescript
// hooks/useDebounced.ts
import { useDeferredValue, useMemo } from 'react';

export function useDebouncedLayout(
  nodes: SimpleTreeNode[],
  expandedIds: string[]
) {
  // React will keep old layout while calculating new one
  const deferredExpandedIds = useDeferredValue(expandedIds);
  
  return useMemo(() => {
    return calculateLayout(nodes, deferredExpandedIds);
  }, [nodes, deferredExpandedIds]);
}
```

---

## 📊 React Flow Optimization

### Node Types Registration

```typescript
// ✅ Define outside component or useMemo
const nodeTypes = {
  function: FunctionNode,
  class: ClassNode,
  call: CallNode,
  file: FileNode,
};

// In component
const CanvasView = () => {
  // ❌ BAD: Creates new object every render
  // const nodeTypes = { enhanced: EnhancedNode };
  
  // ✅ GOOD: Stable reference
  const memoizedNodeTypes = useMemo(() => nodeTypes, []);
  
  return <ReactFlow nodeTypes={memoizedNodeTypes} />;
};
```

### Edge Types

```typescript
// Same pattern for edges
const edgeTypes = {
  custom: CustomEdge,
};

const memoizedEdgeTypes = useMemo(() => edgeTypes, []);
```

### FitView Options

```typescript
// ✅ Define outside component
const fitViewOptions: FitViewOptions = {
  padding: 0.2,
  minZoom: 0.4,
  maxZoom: 1.5,
  duration: 300,
};
```

---

## 🧪 Performance Checklist

- [ ] Node components wrapped in `memo()`
- [ ] Custom comparison function for complex nodes
- [ ] Code editor lazy loaded
- [ ] Layout calculation in `useMemo`
- [ ] State accessed via selectors
- [ ] `nodeTypes` and `edgeTypes` are stable references
- [ ] Heavy computations use `useDeferredValue`
- [ ] Console.log removed from production (`console.log(initialEdges)`)

---

## 📈 Measuring Performance

```typescript
// Add to development
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: string,
  actualDuration: number,
) {
  if (actualDuration > 16) { // More than 1 frame (60fps)
    console.warn(`Slow render: ${id} took ${actualDuration}ms`);
  }
}

// Wrap components to measure
<Profiler id="CanvasView" onRender={onRenderCallback}>
  <CanvasView />
</Profiler>
```

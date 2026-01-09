# Step 2: Left Sidebar - Optimize TreeNode

## Goal
Add memoization and optimize the TreeNode component.

---

## Key Optimizations

### 1. Memoize TreeNode

```typescript
// TreeNode/TreeNode.tsx
import { memo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { AnyNodeTree } from '@/types/project';

interface TreeNodeProps {
  node: AnyNodeTree;
  depth: number;
}

export const TreeNode = memo(function TreeNode({ node, depth }: TreeNodeProps) {
  // Use selectors - only re-render when these specific values change
  const selectedNodeKey = useProjectStore((s) => s.selectedNode?._key);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);

  const isSelected = selectedNodeKey === node._key;
  const isExpanded = expandedNodeIds.includes(node._key);
  const hasChildren = 'children' in node && Array.isArray(node.children) && node.children.length > 0;

  return (
    <div className="tree-node-wrapper">
      <div
        className={`tree-node ${isSelected ? 'selected' : ''}`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={() => setSelectedNode(node)}
      >
        {hasChildren && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              toggleNodeExpansion(node._key);
            }}
            className="tree-node-toggle"
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        )}
        <span className="tree-node-name">{node.name}</span>
      </div>

      {isExpanded && hasChildren && (
        <div className="tree-node-children">
          {(node.children as AnyNodeTree[]).map((child) => (
            <TreeNode key={child._key} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
});
```

---

### 2. Stable Selectors

```typescript
// ❌ BAD: All tree nodes re-render when selectedNode changes structure
const { selectedNode } = useProjectStore();
const isSelected = selectedNode?._key === node._key;

// ✅ GOOD: Only re-renders when the key changes
const selectedNodeKey = useProjectStore((s) => s.selectedNode?._key);
const isSelected = selectedNodeKey === node._key;
```

---

### 3. Consider Virtualization for Large Trees

If trees are very deep (100+ visible nodes), add virtualization:

```typescript
import { useVirtualizer } from '@tanstack/react-virtual';

// See doc/frontend/dashboard/sidebar/overview.md for full example
```

---

## Verification

- [ ] Tree still expands/collapses
- [ ] Selection still works
- [ ] React DevTools shows fewer re-renders

---

## Next Step

👉 [../main/step-01-main-cleanup.md](../main/step-01-main-cleanup.md)

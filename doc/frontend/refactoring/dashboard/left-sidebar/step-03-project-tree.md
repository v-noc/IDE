# Step 3: ProjectTree.tsx Refactoring

## Current State

**File:** `Sidebar/components/ProjectTree.tsx` (136 lines)

### Issues Identified

| Issue | Lines | Impact |
|-------|-------|--------|
| Utility functions in component file | 11-48 | Not reusable, mixed concerns |
| Destructures entire store | 51-60 | Re-renders on any store change |
| DOM manipulation via querySelector | 82-88 | Anti-pattern in React |
| Focus breadcrumb UI in data container | 99-123 | Should be separate component |

---

## Step 3a: Extract Utility Functions

### NEW: `Sidebar/utils/treeUtils.ts`

```typescript
import type { AnyNodeTree, ContainerNodeTree } from '@/types/project';

/**
 * Collect ancestor keys path to a target key (for auto-expansion)
 */
export function collectAncestorKeys(root: AnyNodeTree, targetKey: string): string[] {
  const path: string[] = [];
  
  const dfs = (node: AnyNodeTree): boolean => {
    path.push(node._key);
    if (node._key === targetKey) return true;
    if (node.children) {
      for (const child of node.children as AnyNodeTree[]) {
        if (dfs(child)) return true;
      }
    }
    path.pop();
    return false;
  };
  
  dfs(root);
  path.pop(); // Remove target, keep only ancestors
  return path;
}

/**
 * Determines whether a child node should be rendered in the tree.
 * - Exclude "call" nodes
 * - Exclude "group" nodes with group_type === "call"
 */
export function shouldRenderChild(node: ContainerNodeTree): boolean {
  if (node.node_type === 'call') return false;
  
  if (node.node_type === 'group') {
    const groupType = (node as { group_type?: string }).group_type;
    return groupType !== 'call';
  }
  
  return true;
}
```

---

## Step 3b: Extract Focus Breadcrumb

### NEW: `Sidebar/components/FocusBreadcrumb.tsx`

```typescript
import { memo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';

export const FocusBreadcrumb = memo(function FocusBreadcrumb() {
  // Selectors - only subscribe to what's needed
  const focusedNode = useProjectStore((s) => s.focusedNode);
  const focusStack = useProjectStore((s) => s.focusStack);
  const popFocus = useProjectStore((s) => s.popFocus);
  const clearFocus = useProjectStore((s) => s.clearFocus);

  if (!focusedNode) return null;

  return (
    <div className="flex items-center justify-between px-2 py-1 bg-muted/40 border rounded">
      <div className="text-xs text-muted-foreground truncate">
        Focus: {focusStack.map((n) => n.name).join(' / ')}
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="text-xs px-2 py-0.5 rounded border hover:bg-accent"
          onClick={popFocus}
        >
          Back
        </button>
        <button
          type="button"
          className="text-xs px-2 py-0.5 rounded border hover:bg-accent"
          onClick={clearFocus}
        >
          Clear
        </button>
      </div>
    </div>
  );
});
```

---

## Step 3c: Auto-Expansion Hook

Replace DOM manipulation with React refs:

### NEW: `Sidebar/hooks/useAutoExpandToNode.ts`

```typescript
import { useEffect, useRef } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { collectAncestorKeys } from '../utils/treeUtils';
import type { AnyNodeTree, CallNodeTree } from '@/types/project';

/**
 * When a call node is selected, expand ancestors and scroll to target.
 * Uses refs instead of querySelector for proper React patterns.
 */
export function useAutoExpandToNode(projectTree: AnyNodeTree | null) {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  
  // Track the node to scroll to
  const scrollTargetRef = useRef<string | null>(null);

  useEffect(() => {
    if (!selectedNode || selectedNode.node_type !== 'call' || !projectTree) {
      scrollTargetRef.current = null;
      return;
    }

    const target = (selectedNode as CallNodeTree).target;
    const targetKey = target?._key;
    if (!targetKey) return;

    // Expand ancestors
    const ancestorKeys = collectAncestorKeys(projectTree, targetKey);
    for (const key of ancestorKeys) {
      if (!expandedNodeIds.includes(key)) {
        toggleNodeExpansion(key);
      }
    }

    scrollTargetRef.current = targetKey;
  }, [selectedNode, projectTree, expandedNodeIds, toggleNodeExpansion]);

  // Scroll effect - runs after expansion
  useEffect(() => {
    if (!scrollTargetRef.current) return;
    
    // Use requestAnimationFrame to wait for DOM update
    requestAnimationFrame(() => {
      const el = document.querySelector(`[data-node-key="${scrollTargetRef.current}"]`);
      el?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      scrollTargetRef.current = null;
    });
  });
  
  return scrollTargetRef;
}
```

---

## Step 3d: Simplified ProjectTree

### AFTER: `Sidebar/components/ProjectTree.tsx` (~30 lines)

```typescript
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { TreeNode } from './TreeNode';
import { FocusBreadcrumb } from './FocusBreadcrumb';
import { useAutoExpandToNode } from '../hooks/useAutoExpandToNode';
import { shouldRenderChild } from '../utils/treeUtils';
import type { AnyNodeTree, ContainerNodeTree } from '@/types/project';

interface ProjectTreeProps {
  projectTree: AnyNodeTree;
}

export default function ProjectTree({ projectTree }: ProjectTreeProps) {
  const focusedNode = useProjectStore((s) => s.focusedNode);
  
  // Auto-expand when call node is selected
  useAutoExpandToNode(projectTree);

  const rootNode = (focusedNode ?? projectTree) as ContainerNodeTree;

  return (
    <div className="space-y-1">
      <FocusBreadcrumb />
      
      <ul className="space-y-1">
        <TreeNode
          node={rootNode}
          childFilter={shouldRenderChild}
        />
      </ul>
    </div>
  );
}
```

---

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Lines | 136 | ~30 |
| Utility functions | Embedded | Extracted |
| Store subscriptions | All | Selective |
| DOM queries | querySelector | requestAnimationFrame |
| Focus UI | Embedded | Separate component |

---

## Files Created

- `Sidebar/utils/treeUtils.ts` - Tree utilities
- `Sidebar/components/FocusBreadcrumb.tsx` - Focus navigation UI
- `Sidebar/hooks/useAutoExpandToNode.ts` - Auto-expansion logic

---

## Verification

- [ ] Tree still renders
- [ ] Call selection still scrolls to target
- [ ] Focus breadcrumb still works
- [ ] No console errors

---

## Next Step

👉 [step-04-node-content.md](./step-04-node-content.md)

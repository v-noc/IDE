# Step 4: NodeContent.tsx Refactoring

## Current State

**File:** `TreeNode/NodeContent.tsx` (181 lines)

### Issues Identified

| Issue | Lines | Impact |
|-------|-------|--------|
| Sorting logic in render | 148-164 | Runs every render, should be memoized |
| Style calculation with findNodeByKey | 50-59 | O(n) tree traversal per node |
| Mixed presentation + recursion | 143-176 | Hard to virtualize |
| TooltipProvider per node | 133-142 | Unnecessary wrapper overhead |

---

## Step 4a: Extract Child Sorting

### NEW: `Sidebar/utils/sortChildren.ts`

```typescript
import type { ContainerNodeTree } from '@/types/project';

/**
 * Sort children for folder/project views:
 * 1. Folders first
 * 2. Files second
 * 3. Other types last
 * 4. Alphabetically within each group
 */
export function sortNodeChildren(
  children: ContainerNodeTree[],
  parentType: string
): ContainerNodeTree[] {
  if (parentType !== 'folder' && parentType !== 'project') {
    return children;
  }

  const getRank = (node: ContainerNodeTree): number => {
    if (node.node_type === 'folder') return 0;
    if (node.node_type === 'file') return 1;
    return 2;
  };

  return [...children].sort((a, b) => {
    const rankDiff = getRank(a) - getRank(b);
    if (rankDiff !== 0) return rankDiff;
    return a.name.localeCompare(b.name);
  });
}
```

---

## Step 4b: Memoize Node Style Hook

### NEW: `Sidebar/hooks/useNodeStyle.ts`

```typescript
import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { findNodeByKey } from '@/features/Dashboard/utils/findNode';
import getNodeStyle from '@/features/Dashboard/utils/getNodeStyle';
import type { ContainerNodeTree } from '@/types/project';

/**
 * Get styled properties for a node.
 * Resolves target for call nodes.
 */
export function useNodeStyle(node: ContainerNodeTree) {
  const projectData = useProjectStore((s) => s.projectData);

  return useMemo(() => {
    let effectiveNode = node;
    
    // For call nodes, use target's style
    if (node.target && projectData) {
      const targetNode = findNodeByKey(projectData, node.target._key);
      if (targetNode) {
        effectiveNode = targetNode;
      }
    }

    const style = getNodeStyle(effectiveNode);
    
    return {
      backgroundColor: style.cardColor,
      color: style.color,
      borderColor: style.borderColor,
      iconColor: style.iconColor,
    };
  }, [node, node.target, projectData]);
}
```

---

## Step 4c: Split NodeContent into Pieces

### Structure

```
TreeNode/
├── NodeContent.tsx        # Main content (simplified)
├── NodeRow.tsx           # Single row display
├── NodeChildren.tsx      # Recursive children
└── hooks/
    └── useNodeStyle.ts   # Style calculation
```

### NEW: `TreeNode/NodeRow.tsx`

```typescript
import { memo } from 'react';
import { ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { DynamicIcon } from '@/components/DynamicIcon';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import getIcons from '@/features/Dashboard/utils/getIcons';
import type { ContainerNodeTree, CallNodeTree } from '@/types/project';

interface NodeRowProps {
  node: ContainerNodeTree;
  isOpen: boolean;
  isSelected: boolean;
  hasChildren: boolean;
  iconColor: string;
  onToggle: (e: React.MouseEvent) => void;
  onClick: () => void;
}

export const NodeRow = memo(function NodeRow({
  node,
  isOpen,
  isSelected,
  hasChildren,
  iconColor,
  onToggle,
  onClick,
}: NodeRowProps) {
  const iconName = node.icon || getIcons(
    node.node_type === 'call'
      ? (node as CallNodeTree).target?.node_type ?? 'call'
      : node.node_type
  );

  const row = (
    <li
      onClick={onClick}
      className={cn(
        'flex items-center space-x-1 rounded-md p-1 cursor-pointer',
        'transition-all duration-200 hover:bg-black/5'
      )}
    >
      {/* Toggle */}
      {hasChildren ? (
        <button
          onClick={onToggle}
          className="p-0.5 rounded-md hover:bg-black/10"
          aria-label={isOpen ? 'Collapse' : 'Expand'}
        >
          <ChevronRight
            className={cn(
              'h-4 w-4 transition-transform duration-200',
              isOpen && 'rotate-90'
            )}
          />
        </button>
      ) : (
        <div className="w-4 h-4" />
      )}

      {/* Icon */}
      <DynamicIcon
        iconName={iconName}
        className="h-4 w-4 flex-shrink-0"
        color={iconColor}
      />

      {/* Name */}
      <div className="flex-1 min-w-0">
        <span className={cn(
          'text-sm truncate block',
          isSelected ? 'font-semibold' : 'font-medium'
        )}>
          {node.name}
        </span>
      </div>
    </li>
  );

  // Wrap with tooltip only if has description
  if (node.description) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{row}</TooltipTrigger>
        <TooltipContent side="right">
          <p className="max-w-xs">{node.description}</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  return row;
});
```

### NEW: `TreeNode/NodeChildren.tsx`

```typescript
import { memo, useMemo } from 'react';
import { TreeNode } from '.';
import { sortNodeChildren } from '../../utils/sortChildren';
import type { ContainerNodeTree } from '@/types/project';

interface NodeChildrenProps {
  node: ContainerNodeTree;
  nestingLevel: number;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const NodeChildren = memo(function NodeChildren({
  node,
  nestingLevel,
  childFilter,
  onSelect,
}: NodeChildrenProps) {
  const sortedChildren = useMemo(() => {
    const filtered = (node.children ?? []).filter((n) =>
      childFilter ? childFilter(n) : true
    );
    return sortNodeChildren(filtered, node.node_type);
  }, [node.children, node.node_type, childFilter]);

  if (sortedChildren.length === 0) return null;

  return (
    <ul className="pl-2 pt-1 space-y-1">
      {sortedChildren.map((child) => (
        <TreeNode
          key={child._key}
          node={child}
          nestingLevel={nestingLevel + 1}
          childFilter={childFilter}
          onSelect={onSelect}
        />
      ))}
    </ul>
  );
});
```

---

## Step 4d: Simplified NodeContent

### AFTER: `TreeNode/NodeContent.tsx` (~60 lines)

```typescript
import { memo } from 'react';
import { cn } from '@/lib/utils';
import { Collapsible, CollapsibleContent } from '@/components/ui/collapsible';
import { TooltipProvider } from '@/components/ui/tooltip';
import { NodeRow } from './NodeRow';
import { NodeChildren } from './NodeChildren';
import { useNodeStyle } from './hooks/useNodeStyle';
import type { ContainerNodeTree } from '@/types/project';

interface NodeContentProps {
  node: ContainerNodeTree;
  isOpen: boolean;
  isSelected: boolean;
  isActive: boolean;
  hasChildren: boolean;
  nestingLevel: number;
  handleToggle: (e: React.MouseEvent) => void;
  handleSelectNode: () => void;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const NodeContent = memo(function NodeContent({
  node,
  isOpen,
  isSelected,
  isActive,
  hasChildren,
  nestingLevel,
  handleToggle,
  handleSelectNode,
  childFilter,
  onSelect,
}: NodeContentProps) {
  const style = useNodeStyle(node);

  return (
    <TooltipProvider>
      <Collapsible open={isOpen}>
        <div
          className={cn(
            'rounded-lg p-1 transition-all duration-200 border',
            'mx-1 my-0.5',
            nestingLevel > 0 && 'ml-2',
            isSelected && 'ring-1 ring-blue-500/80',
            isActive && 'ring-2 ring-blue-600'
          )}
          style={{
            backgroundColor: style.backgroundColor,
            color: style.color,
            borderColor: style.borderColor,
          }}
          data-node-key={node._key}
        >
          <NodeRow
            node={node}
            isOpen={isOpen}
            isSelected={isSelected}
            hasChildren={hasChildren}
            iconColor={style.iconColor}
            onToggle={handleToggle}
            onClick={handleSelectNode}
          />

          {hasChildren && (
            <CollapsibleContent>
              <NodeChildren
                node={node}
                nestingLevel={nestingLevel}
                childFilter={childFilter}
                onSelect={onSelect}
              />
            </CollapsibleContent>
          )}
        </div>
      </Collapsible>
    </TooltipProvider>
  );
});
```

---

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Lines in NodeContent | 181 | ~60 |
| Sorting per render | Yes | Memoized |
| TooltipProvider | Every node | Once at top |
| Style calculation | In component | Hook |
| Children rendering | Inline | Separate component |

---

## Files Created

- `Sidebar/utils/sortChildren.ts` - Sorting logic
- `TreeNode/hooks/useNodeStyle.ts` - Style hook
- `TreeNode/NodeRow.tsx` - Row display
- `TreeNode/NodeChildren.tsx` - Recursive children

---

## Verification

- [ ] Nodes still render with correct styles
- [ ] Sorting still works (folders first)
- [ ] Tooltips still show for descriptions
- [ ] Expansion/collapse still works

---

## Next Step

👉 [step-05-use-tree-node.md](./step-05-use-tree-node.md)

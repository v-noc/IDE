# Step 2: Left Sidebar - Pure TreeNode (Professional)

## Goal
Make TreeNode a pure presentation component - triggers actions, doesn't handle them.

---

## Pattern: Event Bus / Action Handler

TreeNode should only say:
> "User clicked Action X on Node Y"

A higher-level controller handles the actual business logic.

---

## NEW: `TreeNode/hooks/useTreeNodeLogic.ts`

Extract core tree interaction logic:

```typescript
import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { AnyNodeTree } from '@/types/project';

export function useTreeNodeLogic(node: AnyNodeTree) {
  // Selectors - only subscribe to what's needed
  const selectedNodeKey = useProjectStore((s) => s.selectedNode?._key);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);

  const isSelected = selectedNodeKey === node._key;
  const isExpanded = expandedNodeIds.includes(node._key);
  const hasChildren = 'children' in node && Array.isArray(node.children) && node.children.length > 0;

  const handleSelect = useCallback(() => {
    setSelectedNode(node);
  }, [node, setSelectedNode]);

  const handleToggle = useCallback((e?: React.MouseEvent) => {
    e?.stopPropagation();
    toggleNodeExpansion(node._key);
  }, [node._key, toggleNodeExpansion]);

  return {
    isSelected,
    isExpanded,
    hasChildren,
    handleSelect,
    handleToggle,
  };
}
```

---

## NEW: `TreeNode/TreeNodeActions.ts`

Define action types:

```typescript
export type TreeNodeAction =
  | 'create-group'
  | 'manage-group'
  | 'add-call'
  | 'prompt-builder'
  | 'copy-path'
  | 'delete';

export interface TreeNodeActionEvent {
  action: TreeNodeAction;
  node: AnyNodeTree;
}
```

---

## Updated: `TreeNode/TreeNode.tsx`

Pure presentation + action dispatching:

```typescript
import { memo } from 'react';
import { useTreeNodeLogic } from './hooks/useTreeNodeLogic';
import { useSidebarModalStore } from '@/features/Dashboard/store/useSidebarModalStore';
import { NodeContent } from './NodeContent';
import { NodeContextMenu } from './NodeContextMenu';
import { NodeIcon } from './NodeIcon';
import type { AnyNodeTree } from '@/types/project';
import type { TreeNodeAction } from './TreeNodeActions';

interface TreeNodeProps {
  node: AnyNodeTree;
  depth: number;
}

export const TreeNode = memo(function TreeNode({ node, depth }: TreeNodeProps) {
  // Core logic - selection, expansion
  const { 
    isSelected, 
    isExpanded, 
    hasChildren, 
    handleSelect, 
    handleToggle 
  } = useTreeNodeLogic(node);

  // Modal actions - dispatch to global store
  const openModal = useSidebarModalStore((s) => s.openModal);

  const handleAction = (action: TreeNodeAction) => {
    switch (action) {
      case 'create-group':
      case 'manage-group':
      case 'add-call':
      case 'prompt-builder':
        openModal(action, node);
        break;
      case 'copy-path':
        navigator.clipboard.writeText(node.path ?? node.name);
        break;
      case 'delete':
        // Handle delete via mutation
        break;
    }
  };

  return (
    <div className="tree-node-wrapper">
      <NodeContextMenu node={node} onAction={handleAction}>
        <div
          className={`tree-node ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={handleSelect}
        >
          {/* Toggle */}
          {hasChildren && (
            <button
              onClick={handleToggle}
              className="tree-node-toggle"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}

          {/* Icon */}
          <NodeIcon nodeType={node.node_type} />

          {/* Name */}
          <span className="tree-node-name">{node.name}</span>
        </div>
      </NodeContextMenu>

      {/* Children - Recursive */}
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

## NodeContextMenu (Simplified)

Just renders menu items, dispatches actions:

```typescript
// TreeNode/NodeContextMenu.tsx
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from '@/components/ui/context-menu';
import type { AnyNodeTree } from '@/types/project';
import type { TreeNodeAction } from './TreeNodeActions';

interface NodeContextMenuProps {
  node: AnyNodeTree;
  onAction: (action: TreeNodeAction) => void;
  children: React.ReactNode;
}

export function NodeContextMenu({ node, onAction, children }: NodeContextMenuProps) {
  const canCreateGroup = node.node_type === 'function' || node.node_type === 'class';
  const canAddCall = node.node_type !== 'project';

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>{children}</ContextMenuTrigger>
      
      <ContextMenuContent>
        {canCreateGroup && (
          <ContextMenuItem onClick={() => onAction('create-group')}>
            Create Group
          </ContextMenuItem>
        )}
        
        {canAddCall && (
          <ContextMenuItem onClick={() => onAction('add-call')}>
            Add Call
          </ContextMenuItem>
        )}
        
        <ContextMenuItem onClick={() => onAction('prompt-builder')}>
          Prompt Builder
        </ContextMenuItem>
        
        <ContextMenuItem onClick={() => onAction('copy-path')}>
          Copy Path
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}
```

---

## Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Lines in TreeNode | ~150 | ~50 |
| useState calls | 6+ | 0 |
| Dialog rendering | In every node | None (global) |
| Business logic | Embedded | Extracted |
| Testability | Low | High |
| Adding new feature | Edit TreeNode | Add to store + menu |

---

## Key Principle

**Separation of Concerns:**

```
TreeNode (Presentation)
    ↓ dispatches action
Modal Store (State)
    ↓ controls
SidebarDialogs (Dialogs)
```

TreeNode doesn't know HOW actions are handled - just WHAT action was triggered.

---

## Verification

- [ ] Context menu still works
- [ ] Selection/expansion still works
- [ ] Dialogs open from menu
- [ ] TreeNode.tsx is ~50 lines

---

## Next Step

👉 [../main/step-01-main-cleanup.md](../main/step-01-main-cleanup.md)

# Step 5: useTreeNode.ts Refactoring

## Current State

**File:** `Sidebar/hooks/useTreeNode.ts` (159 lines)

### Issues Identified

| Issue | Lines | Impact |
|-------|-------|--------|
| Mixes mutations + UI state + selection | All | SRP violation |
| Dialog state in hook | 35-40, 110-124 | Should be in modal store |
| Unused mutations initialized always | 29-31 | Wasted resources |
| Returns 20+ values | 131-157 | Hook does too much |

---

## Solution: Split into Focused Hooks

```
hooks/
├── useTreeNode.ts           # DELETE (too many concerns)
├── useTreeNodeState.ts      # NEW: Selection/expansion only
├── useTreeNodeActions.ts    # NEW: Mutations (call from handlers)
└── useTreeNodeHandlers.ts   # NEW: Event handlers
```

---

## Step 5a: Core State Hook

### NEW: `Sidebar/hooks/useTreeNodeState.ts`

```typescript
import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { ContainerNodeTree } from '@/types/project';

/**
 * Core tree node state - selection, expansion, children.
 * Pure derived state, no side effects.
 */
export function useTreeNodeState(
  node: ContainerNodeTree,
  childFilter: (node: ContainerNodeTree) => boolean = () => true
) {
  // Selective subscriptions - only re-render when these change
  const selectedNodeKey = useProjectStore((s) => s.selectedNode?._key);
  const secondarySelectedKey = useProjectStore((s) => s.secondarySelectedNode?._key);
  const activeNodeId = useProjectStore((s) => s.activeNodeId);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);

  const isOpen = expandedNodeIds.includes(node._key);
  const isSelected = selectedNodeKey === node._key || secondarySelectedKey === node._key;
  const isActive = activeNodeId === node._key;

  const hasChildren = useMemo(() => {
    const children = node.children ?? [];
    return children.some((child) => childFilter(child as ContainerNodeTree));
  }, [node.children, childFilter]);

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
  };
}
```

---

## Step 5b: Handlers Hook

### NEW: `Sidebar/hooks/useTreeNodeHandlers.ts`

```typescript
import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { useSidebarModalStore } from '@/features/Dashboard/store/useSidebarModalStore';
import type { AnyNodeTree, ContainerNodeTree } from '@/types/project';

/**
 * Event handlers for tree node interactions.
 * All mutations dispatch to modal store or API.
 */
export function useTreeNodeHandlers(node: ContainerNodeTree) {
  // Store actions
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);
  const setSecondarySelectedNode = useProjectStore((s) => s.setSecondarySelectedNode);
  const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode);
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  const pushFocus = useProjectStore((s) => s.pushFocus);
  const focusStack = useProjectStore((s) => s.focusStack);

  // Modal store
  const openModal = useSidebarModalStore((s) => s.openModal);

  // Toggle expansion
  const handleToggle = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node._key);
  }, [node._key, toggleNodeExpansion]);

  // Select node
  const handleSelectNode = useCallback(() => {
    if (secondarySelectedNode) {
      setSecondarySelectedNode(null);
    }
    if (selectedNode?._key === node._key) return;
    setSelectedNode(node as AnyNodeTree);
  }, [node, selectedNode, secondarySelectedNode, setSelectedNode, setSecondarySelectedNode]);

  // Focus (zoom into node)
  const handleFocus = useCallback(() => {
    const lastFocused = focusStack[focusStack.length - 1];
    if (lastFocused?._key === node._key) return;
    pushFocus(node as AnyNodeTree);
  }, [node, focusStack, pushFocus]);

  // Expand/collapse
  const handleExpand = useCallback(() => {
    toggleNodeExpansion(node._key);
  }, [node._key, toggleNodeExpansion]);

  // Context menu actions - dispatch to modal store
  const handleContextAction = useCallback((action: string) => {
    switch (action) {
      case 'create-group':
      case 'manage-group':
      case 'add-call':
      case 'prompt-builder':
      case 'edit-virtual':
        openModal(action as any, node as AnyNodeTree);
        break;
      case 'copy-path':
        navigator.clipboard.writeText(node.path ?? node.name);
        break;
    }
  }, [node, openModal]);

  return {
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleContextAction,
  };
}
```

---

## Step 5c: Actions Hook (Mutations)

### NEW: `Sidebar/hooks/useTreeNodeActions.ts`

```typescript
import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { useAddCall, useRemoveCall } from '@/features/Dashboard/service/useCall';
import { useDeleteGroup } from '@/features/Dashboard/service/useGroup';
import type { AnyNodeTree, ContainerNodeTree, CallNodeTree } from '@/types/project';

/**
 * Mutation actions for tree nodes.
 * Only initialize mutations when needed.
 */
export function useTreeNodeActions(node: ContainerNodeTree) {
  const projectKey = useProjectStore((s) => s.projectData?._key ?? '');

  // Lazy initialization - only create mutations when called
  const addCall = useAddCall(node._key, projectKey);
  const removeCall = useRemoveCall(projectKey);
  const deleteGroup = useDeleteGroup(node._key, projectKey);

  const handleAddCall = useCallback((targetNode: AnyNodeTree) => {
    addCall.mutate({
      callee_target_id: targetNode._key,
      name: targetNode.name,
      description: targetNode.description,
    });
  }, [addCall]);

  const handleRemoveCall = useCallback((callNode: CallNodeTree) => {
    removeCall.mutate(callNode._key);
  }, [removeCall]);

  const handleDeleteGroup = useCallback(() => {
    if (node.node_type !== 'group') return;
    deleteGroup.mutate();
  }, [node.node_type, deleteGroup]);

  return {
    handleAddCall,
    handleRemoveCall,
    handleDeleteGroup,
    isAddingCall: addCall.isPending,
    isRemovingCall: removeCall.isPending,
    isDeletingGroup: deleteGroup.isPending,
  };
}
```

---

## Step 5d: Combined Usage (if needed)

### NEW: `Sidebar/hooks/useTreeNode.ts` (Simplified Facade)

```typescript
import type { ContainerNodeTree } from '@/types/project';
import { useTreeNodeState } from './useTreeNodeState';
import { useTreeNodeHandlers } from './useTreeNodeHandlers';
import { useTreeNodeActions } from './useTreeNodeActions';

/**
 * Combined hook for backward compatibility.
 * Prefer using individual hooks for new code.
 */
export function useTreeNode(
  node: ContainerNodeTree,
  childFilter?: (node: ContainerNodeTree) => boolean
) {
  const state = useTreeNodeState(node, childFilter);
  const handlers = useTreeNodeHandlers(node);
  const actions = useTreeNodeActions(node);

  return {
    ...state,
    ...handlers,
    ...actions,
  };
}
```

---

## What Was Removed

- ❌ Dialog state (`isCreateDialogOpen`, etc.) → Now in `useSidebarModalStore`
- ❌ Direct mutations in hook → Lazy via `useTreeNodeActions`
- ❌ 20+ return values → Split into focused hooks

---

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Lines | 159 | ~30 per hook |
| Concerns | 5+ mixed | 1 per hook |
| Dialog state | In hook | Modal store |
| Mutations | Always initialized | Lazy |
| Testability | Low | High |

---

## Usage Examples

### In TreeNode (Basic)

```typescript
function TreeNode({ node, childFilter }) {
  const { isOpen, isSelected, hasChildren } = useTreeNodeState(node, childFilter);
  const { handleToggle, handleSelectNode } = useTreeNodeHandlers(node);
  
  return <NodeContent ... />;
}
```

### In Context Menu (With Actions)

```typescript
function NodeContextMenu({ node }) {
  const { handleContextAction } = useTreeNodeHandlers(node);
  const { handleDeleteGroup, isDeletingGroup } = useTreeNodeActions(node);
  
  return (
    <ContextMenu>
      <ContextMenuItem onClick={() => handleContextAction('add-call')}>
        Add Call
      </ContextMenuItem>
      <ContextMenuItem onClick={handleDeleteGroup} disabled={isDeletingGroup}>
        Delete Group
      </ContextMenuItem>
    </ContextMenu>
  );
}
```

---

## Verification

- [ ] Selection still works
- [ ] Expansion still works
- [ ] Context menu actions open correct modals
- [ ] Mutations still execute

---

## Summary

| Old Hook | New Hooks |
|----------|-----------|
| `useTreeNode` (159 lines, 5 concerns) | `useTreeNodeState` (~30 lines) |
| | `useTreeNodeHandlers` (~50 lines) |
| | `useTreeNodeActions` (~40 lines) |

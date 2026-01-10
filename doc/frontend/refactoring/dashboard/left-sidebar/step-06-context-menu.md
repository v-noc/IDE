# Step 6: NodeContextMenu.tsx Refactoring

## Current State

**File:** `TreeNode/NodeContextMenu.tsx` (110 lines)

### Issues Identified

| Issue | Lines | Impact |
|-------|-------|--------|
| 9 callback props | 16-24 | Tight coupling, prop drilling |
| Dialog state in component | 39 | Should use modal store |
| ConfirmDialog per menu | 98-106 | Duplicated across nodes |
| Logic in render (node_type checks) | 63-95 | Repeated conditionals |

---

## Step 6a: Simplify with Action Pattern

Instead of 9 callbacks, use a single `onAction` dispatch:

### AFTER: `TreeNode/NodeContextMenu.tsx`

```typescript
import { memo } from 'react';
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from '@/components/ui/context-menu';
import { Crosshair, Expand, Group, Link, Trash, FileCode, Copy } from 'lucide-react';
import type { AnyNodeTree } from '@/types/project';

// Action types for type safety
export type NodeAction =
  | 'focus'
  | 'expand'
  | 'add-call'
  | 'remove-call'
  | 'create-group'
  | 'manage-group'
  | 'delete-group'
  | 'prompt-builder'
  | 'copy-path';

interface NodeContextMenuProps {
  children: React.ReactNode;
  node: AnyNodeTree;
  onAction: (action: NodeAction) => void;
}

export const NodeContextMenu = memo(function NodeContextMenu({
  children,
  node,
  onAction,
}: NodeContextMenuProps) {
  const nodeType = node.node_type;
  
  // Determine which actions are available
  const canAddCall = ['function', 'class', 'call', 'file'].includes(nodeType);
  const canRemoveCall = nodeType === 'call' && node.manually_created;
  const isGroup = nodeType === 'group';
  const canCreateGroup = nodeType !== 'project';

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <div>{children}</div>
      </ContextMenuTrigger>

      <ContextMenuContent className="w-48">
        {/* Navigation */}
        <ContextMenuItem onClick={() => onAction('focus')}>
          <Crosshair className="mr-2 h-4 w-4" />
          Focus
        </ContextMenuItem>

        <ContextMenuItem onClick={() => onAction('expand')}>
          <Expand className="mr-2 h-4 w-4" />
          Expand
        </ContextMenuItem>

        <ContextMenuItem onClick={() => onAction('prompt-builder')}>
          <FileCode className="mr-2 h-4 w-4" />
          Build Prompt
        </ContextMenuItem>

        <ContextMenuSeparator />

        {/* Calls */}
        {canAddCall && (
          <ContextMenuItem onClick={() => onAction('add-call')}>
            <Link className="mr-2 h-4 w-4" />
            Add Call
          </ContextMenuItem>
        )}

        {canRemoveCall && (
          <ContextMenuItem onClick={() => onAction('remove-call')}>
            <Trash className="mr-2 h-4 w-4" />
            Remove Call
          </ContextMenuItem>
        )}

        {/* Groups */}
        {isGroup && (
          <>
            <ContextMenuItem onClick={() => onAction('manage-group')}>
              <Group className="mr-2 h-4 w-4" />
              Edit Group
            </ContextMenuItem>
            <ContextMenuItem 
              onClick={() => onAction('delete-group')}
              className="text-destructive"
            >
              <Trash className="mr-2 h-4 w-4" />
              Delete Group
            </ContextMenuItem>
          </>
        )}

        {canCreateGroup && (
          <ContextMenuItem onClick={() => onAction('create-group')}>
            <Group className="mr-2 h-4 w-4" />
            Create Group
          </ContextMenuItem>
        )}

        <ContextMenuSeparator />

        {/* Utility */}
        <ContextMenuItem onClick={() => onAction('copy-path')}>
          <Copy className="mr-2 h-4 w-4" />
          Copy Path
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
});
```

---

## Step 6b: Move ConfirmDialog to SidebarDialogs

The delete confirmation should live with other dialogs:

### UPDATE: `Sidebar/components/SidebarDialogs.tsx`

```typescript
import { useSidebarModalStore } from '@/features/Dashboard/store/useSidebarModalStore';
import { ConfirmDialog } from '@/components/ConfirmDialog';
import { useTreeNodeActions } from '../hooks/useTreeNodeActions';
// ... other imports

export function SidebarDialogs() {
  const { activeModal, targetNode, closeModal } = useSidebarModalStore();

  // Get delete action for current target
  const { handleDeleteGroup, isDeletingGroup } = useTreeNodeActions(
    targetNode as ContainerNodeTree
  );

  if (!targetNode) return null;

  return (
    <>
      {/* Existing dialogs... */}
      
      {/* Delete Group Confirmation */}
      <ConfirmDialog
        open={activeModal === 'delete-group'}
        onOpenChange={(open) => !open && closeModal()}
        title="Delete this group?"
        description="This action cannot be undone."
        confirmLabel="Delete"
        actionClassName="bg-destructive text-destructive-foreground hover:bg-destructive/90"
        onConfirm={() => {
          handleDeleteGroup();
          closeModal();
        }}
        isLoading={isDeletingGroup}
      />
    </>
  );
}
```

---

## Step 6c: Usage in TreeNode

```typescript
// TreeNode/index.tsx
import { NodeContextMenu, type NodeAction } from './NodeContextMenu';
import { useTreeNodeHandlers } from '../hooks/useTreeNodeHandlers';

function TreeNode({ node, ...props }) {
  const { handleContextAction } = useTreeNodeHandlers(node);
  
  const onAction = (action: NodeAction) => {
    handleContextAction(action);
  };

  return (
    <NodeContextMenu node={node} onAction={onAction}>
      <NodeContent ... />
    </NodeContextMenu>
  );
}
```

---

## Before vs After

| Metric | Before | After |
|--------|--------|-------|
| Props | 9 callbacks | 1 `onAction` |
| Dialog state | In component | Modal store |
| ConfirmDialog | Per menu instance | Single in SidebarDialogs |
| Lines | 110 | ~80 |
| Memoized | No | Yes |

---

## Verification

- [ ] Context menu still opens
- [ ] All actions still work
- [ ] Delete confirmation shows
- [ ] Delete actually deletes

---

## Summary: Complete Sidebar Refactoring

| Step | File | Before | After |
|------|------|--------|-------|
| 1 | Modal store | - | `useSidebarModalStore.ts` |
| 2 | TreeNode | 150+ lines | ~50 lines |
| 3 | ProjectTree | 136 lines | ~30 lines |
| 4 | NodeContent | 181 lines | ~60 lines |
| 5 | useTreeNode | 159 lines | 3 hooks × ~30 lines |
| 6 | NodeContextMenu | 110 lines, 9 props | ~80 lines, 1 prop |

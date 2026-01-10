# Step 1: Left Sidebar - Modal Store Pattern (Professional)

## Goal
Eliminate the "Dialog Explosion" problem by hoisting modal state globally.

---

## 🚨 Problem: Dialog in Every Node

Current anti-pattern - every TreeNode has its own dialog state:

```typescript
// ❌ CURRENT: Every node instance has these
const TreeNode = ({ node }) => {
  const [isCreateGroupsDialogOpen, setIsCreateGroupsDialogOpen] = useState(false);
  const [isAddCallDialogOpen, setIsAddCallDialogOpen] = useState(false);
  const [isManageGroupDialogOpen, setIsManageGroupDialogOpen] = useState(false);
  // ... more useState for each dialog

  return (
    <>
      <NodeContent />
      <CreateGroupsDialog 
        isOpen={isCreateGroupsDialogOpen} 
        onClose={() => setIsCreateGroupsDialogOpen(false)} 
      />
      <AddCallDialog isOpen={isAddCallDialogOpen} {...} />
      {/* 500 nodes = 500 hidden dialog instances in memory! */}
    </>
  );
};
```

**Impact:**
- 500 files = 500 dialog closures in memory
- Heavy DOM weight
- Hard to virtualize
- SRP violation - TreeNode knows about Groups, Calls, Prompts, etc.

---

## ✅ Solution: Global Modal Store

Only **ONE** instance of each dialog exists, controlled by a global store.

### NEW: `features/Dashboard/store/useSidebarModalStore.ts`

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { AnyNodeTree } from '@/types/project';

// All modal types in the sidebar
type ModalType = 
  | 'create-group' 
  | 'manage-group' 
  | 'add-call' 
  | 'prompt-builder' 
  | 'edit-virtual-folder'
  | 'select-node'
  | null;

interface SidebarModalState {
  // State
  activeModal: ModalType;
  targetNode: AnyNodeTree | null;
  
  // Actions
  openModal: (type: ModalType, node: AnyNodeTree) => void;
  closeModal: () => void;
}

export const useSidebarModalStore = create<SidebarModalState>()(
  devtools(
    (set) => ({
      activeModal: null,
      targetNode: null,

      openModal: (type, node) => set({ 
        activeModal: type, 
        targetNode: node 
      }),

      closeModal: () => set({ 
        activeModal: null, 
        targetNode: null 
      }),
    }),
    { name: 'sidebar-modals' }
  )
);

// Selectors for performance
export const useActiveModal = () => useSidebarModalStore((s) => s.activeModal);
export const useTargetNode = () => useSidebarModalStore((s) => s.targetNode);
export const useOpenModal = () => useSidebarModalStore((s) => s.openModal);
export const useCloseModal = () => useSidebarModalStore((s) => s.closeModal);
```

---

## NEW: `Sidebar/components/SidebarDialogs.tsx`

Render dialogs **once** at the sidebar root:

```typescript
import { useSidebarModalStore } from '@/features/Dashboard/store/useSidebarModalStore';
import CreateGroupsDialog from './dialogs/CreateGroupsDialog';
import SelectNodeDialog from './SelectNodeDialog';
import AddCallDialog from './dialogs/AddCallDialog';
import PromptBuilderDialog from './dialogs/PromptBuilderDialog';
import ManageGroupDialog from './dialogs/ManageGroupDialog';

export function SidebarDialogs() {
  const { activeModal, targetNode, closeModal } = useSidebarModalStore();

  // No node = no dialogs
  if (!targetNode) return null;

  return (
    <>
      <CreateGroupsDialog
        open={activeModal === 'create-group'}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />

      <SelectNodeDialog
        open={activeModal === 'select-node'}
        onOpenChange={(open) => !open && closeModal()}
        sourceNode={targetNode}
      />

      <AddCallDialog
        open={activeModal === 'add-call'}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />

      <PromptBuilderDialog
        open={activeModal === 'prompt-builder'}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />

      <ManageGroupDialog
        open={activeModal === 'manage-group'}
        onOpenChange={(open) => !open && closeModal()}
        node={targetNode}
      />
    </>
  );
}
```

---

## Updated: `Sidebar/components/SideBar.tsx`

Now clean and composable:

```typescript
import { SidebarDialogs } from './SidebarDialogs';
import { ProjectTree } from './ProjectTree';
import { SearchInput } from './SearchInput';
import { useTreeFilter } from '../hooks/useTreeFilter';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';

export default function SideBar() {
  const projectData = useProjectStore((s) => s.projectData);
  const { filteredNodes, searchQuery, setSearchQuery } = useTreeFilter(
    projectData?.children
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search files..."
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto">
        <ProjectTree nodes={filteredNodes} />
      </div>

      {/* Dialogs - Single instance at root */}
      <SidebarDialogs />
    </div>
  );
}
```

---

## Benefits

| Metric | Before | After |
|--------|--------|-------|
| Dialog instances | 500+ (one per node) | 5 (one per type) |
| useState in TreeNode | 6+ | 0 |
| TreeNode lines | ~150 | ~50 |
| Memory usage | High | Low |
| Virtualization ready | No | Yes |

---

## Verification

- [ ] Dialogs still open from context menu
- [ ] Correct node is passed to dialog
- [ ] Dialog closes properly
- [ ] Memory usage is lower (check React DevTools)

---

## Next Step

👉 [step-02-tree-node.md](./step-02-tree-node.md) - Clean TreeNode component

# Step 8: Split Project Store into Slices

## Goal
Break `useProjectStore.ts` (129 lines) into focused slices.

## Why
The current store mixes:
- Selection state (selectedNode, secondarySelectedNode)
- Focus/navigation state (focusStack, focusedNode)
- UI state (expandedNodeIds)
- Data (projectData)

Slices make it easier to understand and test.

---

## New Structure

```
store/
├── useProjectStore.ts     # Combined store (entry point)
└── slices/
    ├── selectionSlice.ts  # Selected nodes
    ├── focusSlice.ts      # Focus stack navigation
    ├── uiSlice.ts         # Expanded nodes, etc.
    └── dataSlice.ts       # Project data
```

---

## Step 8a: Create Selection Slice

### NEW: `store/slices/selectionSlice.ts`

```typescript
import { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';

export interface SelectionSlice {
  selectedNode: AnyNodeTree | null;
  secondarySelectedNode: AnyNodeTree | null;
  selectedDocumentId: string | null;
  
  setSelectedNode: (node: AnyNodeTree | null) => void;
  setSecondarySelectedNode: (node: AnyNodeTree | null) => void;
  setSelectedDocumentId: (id: string | null) => void;
  clearSelection: () => void;
}

export const createSelectionSlice: StateCreator<
  SelectionSlice,
  [['zustand/immer', never], ['zustand/devtools', never]]
> = (set) => ({
  selectedNode: null,
  secondarySelectedNode: null,
  selectedDocumentId: null,

  setSelectedNode: (node) => set({ selectedNode: node }),
  setSecondarySelectedNode: (node) => set({ secondarySelectedNode: node }),
  setSelectedDocumentId: (id) => set({ selectedDocumentId: id }),
  clearSelection: () => set({ 
    selectedNode: null, 
    secondarySelectedNode: null,
    selectedDocumentId: null,
  }),
});
```

---

## Step 8b: Create Focus Slice

### NEW: `store/slices/focusSlice.ts`

```typescript
import { StateCreator } from 'zustand';
import type { AnyNodeTree } from '@/types/project';

export interface FocusSlice {
  focusStack: AnyNodeTree[];
  focusedNode: AnyNodeTree | null;
  
  pushFocus: (node: AnyNodeTree) => void;
  popFocus: () => void;
  clearFocus: () => void;
}

export const createFocusSlice: StateCreator<
  FocusSlice,
  [['zustand/immer', never], ['zustand/devtools', never]]
> = (set) => ({
  focusStack: [],
  focusedNode: null,

  pushFocus: (node) => set((state) => {
    state.focusStack.push(node);
    state.focusedNode = node;
  }),

  popFocus: () => set((state) => {
    state.focusStack.pop();
    state.focusedNode = state.focusStack[state.focusStack.length - 1] ?? null;
  }),

  clearFocus: () => set({ focusStack: [], focusedNode: null }),
});
```

---

## Step 8c: Create UI Slice

### NEW: `store/slices/uiSlice.ts`

```typescript
import { StateCreator } from 'zustand';

export interface UISlice {
  expandedNodeIds: string[];
  activeNodeId: string | null;
  
  toggleNodeExpansion: (nodeId: string) => void;
  expandNode: (nodeId: string) => void;
  collapseNode: (nodeId: string) => void;
  setActiveNodeId: (id: string | null) => void;
}

export const createUISlice: StateCreator<
  UISlice,
  [['zustand/immer', never], ['zustand/devtools', never]]
> = (set) => ({
  expandedNodeIds: [],
  activeNodeId: null,

  toggleNodeExpansion: (nodeId) => set((state) => {
    const index = state.expandedNodeIds.indexOf(nodeId);
    if (index > -1) {
      state.expandedNodeIds.splice(index, 1);
    } else {
      state.expandedNodeIds.push(nodeId);
    }
  }),

  expandNode: (nodeId) => set((state) => {
    if (!state.expandedNodeIds.includes(nodeId)) {
      state.expandedNodeIds.push(nodeId);
    }
  }),

  collapseNode: (nodeId) => set((state) => {
    const index = state.expandedNodeIds.indexOf(nodeId);
    if (index > -1) {
      state.expandedNodeIds.splice(index, 1);
    }
  }),

  setActiveNodeId: (id) => set({ activeNodeId: id }),
});
```

---

## Step 8d: Create Data Slice

### NEW: `store/slices/dataSlice.ts`

```typescript
import { StateCreator } from 'zustand';
import type { AnyNodeTree, ProjectNodeTree } from '@/types/project';
import { findNodeByKey } from '@/features/Dashboard/utils/findNode';

export interface DataSlice {
  projectData: ProjectNodeTree | null;
  setProjectData: (data: ProjectNodeTree | null) => void;
}

// This slice needs access to focus slice to remap nodes
type CombinedState = DataSlice & { 
  focusStack: AnyNodeTree[];
  focusedNode: AnyNodeTree | null;
  selectedNode: AnyNodeTree | null;
};

export const createDataSlice: StateCreator<
  CombinedState,
  [['zustand/immer', never], ['zustand/devtools', never]],
  [],
  DataSlice
> = (set) => ({
  projectData: null,

  setProjectData: (data) => set((state) => {
    state.projectData = data;
    
    // Remap focus stack to new tree
    if (data && state.focusStack.length > 0) {
      const remapped = state.focusStack
        .map((n) => findNodeByKey(data, n._key))
        .filter((n): n is AnyNodeTree => n != null);
      state.focusStack = remapped;
      state.focusedNode = remapped[remapped.length - 1] ?? null;
    } else if (!data) {
      state.focusStack = [];
      state.focusedNode = null;
    }
    
    // Remap selected node
    if (data && state.selectedNode) {
      state.selectedNode = findNodeByKey(data, state.selectedNode._key) ?? null;
    } else if (!data) {
      state.selectedNode = null;
    }
  }),
});
```

---

## Step 8e: Combine Slices

### Updated: `store/useProjectStore.ts`

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

import { createSelectionSlice, SelectionSlice } from './slices/selectionSlice';
import { createFocusSlice, FocusSlice } from './slices/focusSlice';
import { createUISlice, UISlice } from './slices/uiSlice';
import { createDataSlice, DataSlice } from './slices/dataSlice';

type ProjectStore = SelectionSlice & FocusSlice & UISlice & DataSlice;

const useProjectStore = create<ProjectStore>()(
  devtools(
    immer((...a) => ({
      ...createSelectionSlice(...a),
      ...createFocusSlice(...a),
      ...createUISlice(...a),
      ...createDataSlice(...a),
    })),
    { name: 'project-store' }
  )
);

export default useProjectStore;
```

---

## Verification

- [ ] Store still works (same interface)
- [ ] Sidebar navigation works
- [ ] Canvas shows correct data
- [ ] Selection highlights properly

---

## 🎉 Done!

You've completed the refactoring plan. Your codebase now has:

- ✅ Centralized query keys
- ✅ Unified code/logs services with shared cache
- ✅ React Context for socket
- ✅ Socket events syncing to React Query
- ✅ Cleaner Canvas components
- ✅ Performance optimizations
- ✅ Organized store slices

---

## What's Next?

Consider these additional improvements:

1. **Add tests** - Unit tests for hooks and services
2. **Error boundaries** - Catch errors gracefully
3. **Remove old files** - Delete the migrated code
4. **TypeScript strict mode** - Enable for better safety

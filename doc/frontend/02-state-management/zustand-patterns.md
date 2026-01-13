# Zustand Patterns

## 🎯 Goal

Master Zustand patterns for clean, maintainable client state.

---

## 🧱 The Slice Pattern

Split large stores into focused slices:

```typescript
// store/slices/selectionSlice.ts
import { StateCreator } from 'zustand';

export interface SelectionSlice {
  selectedNode: AnyNodeTree | null;
  secondaryNode: AnyNodeTree | null;
  setSelectedNode: (node: AnyNodeTree) => void;
  setSecondaryNode: (node: AnyNodeTree | null) => void;
  clearSelection: () => void;
}

export const createSelectionSlice: StateCreator<
  SelectionSlice,
  [['zustand/immer', never]]
> = (set) => ({
  selectedNode: null,
  secondaryNode: null,
  setSelectedNode: (node) => set({ selectedNode: node }),
  setSecondaryNode: (node) => set({ secondaryNode: node }),
  clearSelection: () => set({ selectedNode: null, secondaryNode: null }),
});
```

```typescript
// store/slices/focusSlice.ts
export interface FocusSlice {
  focusStack: AnyNodeTree[];
  pushFocus: (node: AnyNodeTree) => void;
  popFocus: () => void;
  clearFocus: () => void;
}

export const createFocusSlice: StateCreator<
  FocusSlice,
  [['zustand/immer', never]]
> = (set) => ({
  focusStack: [],
  pushFocus: (node) => set((state) => {
    state.focusStack.push(node);
  }),
  popFocus: () => set((state) => {
    state.focusStack.pop();
  }),
  clearFocus: () => set({ focusStack: [] }),
});
```

```typescript
// store/useProjectStore.ts - Combine slices
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { createSelectionSlice, SelectionSlice } from './slices/selectionSlice';
import { createFocusSlice, FocusSlice } from './slices/focusSlice';

type ProjectStore = SelectionSlice & FocusSlice;

const useProjectStore = create<ProjectStore>()(
  devtools(
    immer((...args) => ({
      ...createSelectionSlice(...args),
      ...createFocusSlice(...args),
    })),
    { name: 'project-store' }
  )
);

export default useProjectStore;
```

---

## 🎣 Selector Pattern

### Problem: Re-renders

```typescript
// ❌ BAD: Component re-renders on ANY store change
const Component = () => {
  const store = useProjectStore();
  return <div>{store.selectedNode?.name}</div>;
};
```

### Solution: Use Selectors

```typescript
// ✅ GOOD: Only re-renders when selectedNode changes
const Component = () => {
  const selectedNode = useProjectStore((state) => state.selectedNode);
  return <div>{selectedNode?.name}</div>;
};
```

### Multiple Values

```typescript
// ✅ Use shallow comparison for multiple values
import { shallow } from 'zustand/shallow';

const Component = () => {
  const { selectedNode, focusStack } = useProjectStore(
    (state) => ({
      selectedNode: state.selectedNode,
      focusStack: state.focusStack,
    }),
    shallow
  );
  return <div>...</div>;
};
```

### Derived State

```typescript
// ✅ Compute derived state in selector
const Component = () => {
  const canGoBack = useProjectStore(
    (state) => state.focusStack.length > 1
  );
  const currentFocus = useProjectStore(
    (state) => state.focusStack[state.focusStack.length - 1]
  );
  return <button disabled={!canGoBack}>Back</button>;
};
```

---

## 🔒 Actions Pattern

### Keep Actions in the Store

```typescript
// ✅ Define actions inside the store
const useProjectStore = create<ProjectState>()(
  devtools(
    immer((set, get) => ({
      selectedNode: null,
      projectData: null,
      
      // Simple action
      setSelectedNode: (node) => set({ selectedNode: node }),
      
      // Action that reads current state
      selectNodeById: (nodeId: string) => {
        const { projectData } = get();
        if (projectData) {
          const node = findNodeByKey(projectData, nodeId);
          if (node) set({ selectedNode: node });
        }
      },
      
      // Async action
      loadAndSelect: async (nodeId: string) => {
        const node = await fetchNode(nodeId);
        set({ selectedNode: node });
      },
    }))
  )
);
```

---

## 🔄 Reset Pattern

```typescript
interface ProjectState {
  // State
  selectedNode: AnyNodeTree | null;
  focusStack: AnyNodeTree[];
  expandedNodeIds: string[];
  
  // Actions
  setSelectedNode: (node: AnyNodeTree) => void;
  
  // Reset
  reset: () => void;
}

// Define initial state separately
const initialState = {
  selectedNode: null,
  focusStack: [],
  expandedNodeIds: [],
};

const useProjectStore = create<ProjectState>()(
  immer((set) => ({
    ...initialState,
    
    setSelectedNode: (node) => set({ selectedNode: node }),
    
    // Reset to initial state (useful when changing projects)
    reset: () => set(initialState),
  }))
);
```

---

## 📖 Next Steps

- **[shared-state.md](./shared-state.md)** - Patterns for code/logs shared state

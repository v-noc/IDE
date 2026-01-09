# State Management Overview

## 🎯 Goal

Understand **what state goes where** and keep your app predictable.

---

## 🧠 The Golden Rule

> **Server State** ≠ **Client State**

| Type | What is it? | Tool | Example |
|------|-------------|------|---------|
| **Server State** | Data from API | TanStack Query | Project list, code content, logs |
| **Client State** | UI-only data | Zustand | Selected node, expanded items, theme |

---

## 📊 State Decision Tree

```
┌─────────────────────────────────────────┐
│         Where does this data           │
│              come from?                 │
└─────────────────────┬───────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ▼                           ▼
   From Server?                 From User?
        │                           │
        ▼                           ▼
  TanStack Query              Is it shared?
        │                           │
        │               ┌───────────┴───────────┐
        │               ▼                       ▼
        │           Multiple                 Single
        │          components?              component?
        │               │                       │
        │               ▼                       ▼
        │           Zustand              useState/useReducer
        │
        └───────────────────────────────────────┘
```

---

## 🏪 Zustand for Client State

### When to Use Zustand

- ✅ UI state shared across components (selected node, expanded items)
- ✅ Theme preferences
- ✅ User preferences that don't need server sync
- ✅ Navigation state (focus stack)

### Store Organization (Slice Pattern)

Instead of one giant store, split by domain:

```typescript
// store/useProjectStore.ts - Project-related UI state
interface ProjectState {
  selectedNode: AnyNodeTree | null;
  focusStack: AnyNodeTree[];
  expandedNodeIds: string[];
  // Actions
  setSelectedNode: (node: AnyNodeTree) => void;
  pushFocus: (node: AnyNodeTree) => void;
  popFocus: () => void;
}

// store/useThemeStore.ts - Theme/appearance state
interface ThemeState {
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

// store/useUIStore.ts - Generic UI state
interface UIState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
}
```

### Zustand Best Practices

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

// ✅ Use devtools for debugging + immer for immutable updates
const useProjectStore = create<ProjectState>()(
  devtools(
    immer((set) => ({
      selectedNode: null,
      focusStack: [],
      expandedNodeIds: [],
      
      setSelectedNode: (node) => set({ selectedNode: node }),
      
      // Immer allows "mutating" syntax
      pushFocus: (node) => set((state) => {
        state.focusStack.push(node);
      }),
      
      popFocus: () => set((state) => {
        state.focusStack.pop();
      }),
    })),
    { name: 'project-store' } // DevTools name
  )
);
```

---

## 🔄 TanStack Query for Server State

### When to Use TanStack Query

- ✅ Data fetched from your API
- ✅ Data that needs caching
- ✅ Data that multiple components display
- ✅ Data that needs background refetching

### Query Organization

```typescript
// service/useProject.tsx

// 1. Define the fetch function separately
const getProjectTree = async (key: string): Promise<ProjectNodeTree> => {
  return api(`/projects/${key}`);
};

// 2. Create the query hook
export const useProjectTree = (projectKey: string) => {
  return useQuery({
    queryKey: ['projectTree', projectKey],  // Cache key
    queryFn: () => getProjectTree(projectKey),
    enabled: !!projectKey,  // Only fetch when key exists
    staleTime: 5 * 60 * 1000,  // Cache for 5 minutes
  });
};

// 3. Create mutation hooks for updates
export const useUpdateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateProject,
    onSuccess: (_, variables) => {
      // Invalidate related queries
      queryClient.invalidateQueries({
        queryKey: ['projectTree', variables.projectKey]
      });
    },
  });
};
```

---

## 🔗 Connecting Zustand and TanStack Query

### Pattern: Sync Server Data to Zustand

When you need derived state from server data:

```typescript
// In your component
function Dashboard({ projectKey }: { projectKey: string }) {
  const { data: projectTree } = useProjectTree(projectKey);
  const setProjectData = useProjectStore((s) => s.setProjectData);
  
  // Sync to Zustand when data changes
  useEffect(() => {
    if (projectTree) {
      setProjectData(projectTree);
    }
  }, [projectTree, setProjectData]);
  
  // ...
}
```

### Pattern: Custom Hook Combining Both

```typescript
// hooks/useProjectNavigation.ts
export function useProjectNavigation(projectKey: string) {
  // Server state
  const { data: project, isLoading } = useProjectTree(projectKey);
  
  // Client state
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const pushFocus = useProjectStore((s) => s.pushFocus);
  const popFocus = useProjectStore((s) => s.popFocus);
  
  // Derived state
  const canGoBack = useProjectStore((s) => s.focusStack.length > 1);
  
  return {
    project,
    isLoading,
    selectedNode,
    pushFocus,
    popFocus,
    canGoBack,
  };
}
```

---

## 📋 State Checklist

Before adding new state, ask:

1. **Does it come from the server?** → TanStack Query
2. **Is it only used in one component?** → `useState`
3. **Is it complex object updates?** → `useReducer`
4. **Is it shared across components?** → Zustand
5. **Is it derived from server data?** → TanStack Query select

---

## 📖 Next Steps

- **[zustand-patterns.md](./zustand-patterns.md)** - Deep dive into Zustand patterns
- **[react-query-patterns.md](./react-query-patterns.md)** - TanStack Query best practices
- **[shared-state.md](./shared-state.md)** - Handling shared state (code, logs)

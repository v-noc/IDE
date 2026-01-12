# Step 1: Right Sidebar - Hooks Architecture

## Goal
Architect the Right Sidebar hooks to follow the Single Responsibility Principle, matching the standard set by the Left Sidebar refactoring.

**Pattern:** Split hooks into **State** (Derived), **Actions** (Mutations), and **Handlers** (Events).

---

## Current State

**File:** `RightSidebar/index.tsx` (Contains mixed logic)

### Issues
- `onChangeTheme` mixes state updates + API logic.
- `onChangeBasicInfo` mixes form logic + optimistic updates + API calls.
- `updateNodeInTree` helper is mixed with component logic.

---

## Proposed Solution

```
hooks/
├── useRightSidebarState.ts      # Derived state (readonly)
├── useRightSidebarActions.ts    # Mutations (API calls)
└── useRightSidebarHandlers.ts   # Event handlers (connecting UI to Actions/Store)
```

---

## Step 1a: Actions Hook (Mutations)

### NEW: `RightSidebar/hooks/useRightSidebarActions.ts`

Responsible **only** for executing side effects (API calls) and complex store updates (tree traversal).

```typescript
import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { useUpdateBasicInfo } from '../../service/useContainer';
import type { AnyNodeTree, ProjectNodeTree, ThemeConfig } from '@/types/project';

// Helper: Pure function to walk tree (extracted outside hook)
function updateNodeInTree(
  tree: ProjectNodeTree,
  key: string,
  updater: (node: AnyNodeTree) => AnyNodeTree
): ProjectNodeTree {
  // ... implementation ...
  return tree; // placeholder
}

export function useRightSidebarActions() {
  const { selectedNode, projectData, setProjectData, setSelectedNode } = useProjectStore();
  const { mutate: updateBasicInfoApi } = useUpdateBasicInfo(selectedNode?._key ?? '');

  const updateTheme = useCallback((theme: ThemeConfig) => {
    if (!selectedNode || !projectData) return;
    // 1. Optimistic Update Tree
    const updatedTree = updateNodeInTree(projectData, selectedNode._key, (n) => ({ ...n, theme_config: theme }));
    setProjectData(updatedTree);
    
    // 2. Update Selection
    setSelectedNode({ ...selectedNode, theme_config: theme } as AnyNodeTree);
    
    // 3. API Call (if theme is saved to backend, or just local state)
    // ...
  }, [projectData, selectedNode, setProjectData, setSelectedNode]);

  const updateBasicInfo = useCallback((info: { name: string; description: string; icon: string }) => {
    if (!selectedNode || !projectData) return;
    
    // 1. Optimistic Update Tree
    const updatedTree = updateNodeInTree(projectData, selectedNode._key, (n) => ({ ...n, ...info }));
    setProjectData(updatedTree);

    // 2. Update Selection
    setSelectedNode({ ...selectedNode, ...info } as AnyNodeTree);

    // 3. API Call
    updateBasicInfoApi(info);
  }, [projectData, selectedNode, setProjectData, setSelectedNode, updateBasicInfoApi]);

  return {
    updateTheme,
    updateBasicInfo,
  };
}
```

---

## Step 1b: Handlers Hook (Events)

### NEW: `RightSidebar/hooks/useRightSidebarHandlers.ts`

Responsible for mapping UI events to Actions. Validates inputs if needed.

```typescript
import { useCallback } from 'react';
import { useRightSidebarActions } from './useRightSidebarActions';
import type { BasicInfoData, CustomizationData } from './types'; // Define types

export function useRightSidebarHandlers() {
  const { updateTheme, updateBasicInfo } = useRightSidebarActions();

  const handleThemeChange = useCallback((data: CustomizationData) => {
    // Transform form data to domain object
    const theme = {
      iconColor: data.iconColor,
      cardColor: data.cardColor,
      // ... map fields
    };
    updateTheme(theme);
  }, [updateTheme]);

  const handleBasicInfoChange = useCallback((data: BasicInfoData) => {
    // Validation logic (if any) could go here
    updateBasicInfo({
      name: data.name,
      description: data.description ?? '',
      icon: data.icon ?? '', // Default handling
    });
  }, [updateBasicInfo]);

  return {
    handleThemeChange,
    handleBasicInfoChange
  };
}
```

---

## Step 1c: State Hook (Derived)

### NEW: `RightSidebar/hooks/useRightSidebarState.ts`

Responsible for preparing the initial state for the form.

```typescript
import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { getIcons } from '@/features/Dashboard/utils';

export function useRightSidebarState() {
  const selectedNode = useProjectStore((s) => s.selectedNode);

  return useMemo(() => ({
    initialBasicInfo: {
      name: selectedNode?.name ?? '',
      description: selectedNode?.description ?? '',
      icon: selectedNode ? (selectedNode.icon || getIcons(selectedNode.node_type)) : '',
    },
    initialCustomization: {
      iconColor: selectedNode?.theme_config?.iconColor,
      // ... map fields
    },
    // Useful derived flags
    hasSelection: !!selectedNode,
    nodeType: selectedNode?.node_type,
  }), [selectedNode]);
}
```

---

## Verification

- [ ] Separation of Concerns: Actions don't know about form events; Handlers don't know about Store internals.
- [ ] No Logic Change: The net effect of `handleThemeChange` -> `updateTheme` is identical to the old `onChangeTheme`.

---

## Next Step
👉 [step-02-prop-drilling.md](./step-02-prop-drilling.md)

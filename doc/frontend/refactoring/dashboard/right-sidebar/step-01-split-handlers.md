# Step 1: Right Sidebar - Extract Handlers

## Goal
Move update handlers out of `RightSidebar/index.tsx` (245 lines) into a dedicated hook.

## Why
The component mixes:
- Tree mutation logic (`updateNodeInTree`)
- Theme change handlers (`onChangeTheme`)
- Basic info handlers (`onChangeBasicInfo`)
- JSX rendering

---

## Current State

```typescript
// RightSidebar/index.tsx
export const RightSidebar = ({ className, onToggle }) => {
  const { selectedNode, projectData, setProjectData, setSelectedNode } = useProjectStore();
  const { mutate: updateBasicInfo } = useUpdateBasicInfo(selectedNode?._key ?? '');

  // ❌ 60+ lines of handler logic mixed with component
  const updateNodeInTree = useCallback(...);
  const onChangeTheme = useCallback(...);
  const onChangeBasicInfo = useCallback(...);
  const sidebarProps = useMemo(...);

  return ( ... );
};
```

---

## What to Create

### NEW: `RightSidebar/hooks/useNodeUpdates.ts`

```typescript
import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { AnyNodeTree, ProjectNodeTree, ThemeConfig } from '@/types/project';
import { getIcons } from '@/features/Dashboard/utils';
import { useUpdateBasicInfo } from '../../../service/useContainer';

type NodeWithChildren = AnyNodeTree & { children?: AnyNodeTree[] };

export interface BasicInfoData {
  name: string;
  description?: string;
  icon?: string;
}

export interface CustomizationData {
  iconColor?: string;
  cardColor?: string;
  navbarColor?: string;
  backgroundColor?: string;
  leftSidebarColor?: string;
  rightSidebarColor?: string;
  textColor?: string;
}

/**
 * Update a node in the tree immutably
 */
function updateNodeInTree(
  tree: ProjectNodeTree,
  key: string,
  updater: (node: AnyNodeTree) => AnyNodeTree
): ProjectNodeTree {
  const walk = (node: AnyNodeTree): AnyNodeTree => {
    if (node._key === key) {
      return updater({ ...node });
    }
    const children = (node as NodeWithChildren).children;
    if (Array.isArray(children) && children.length) {
      return {
        ...node,
        children: children.map((c) => walk(c)),
      } as AnyNodeTree;
    }
    return node;
  };

  return walk(tree) as ProjectNodeTree;
}

export function useNodeUpdates() {
  const { selectedNode, projectData, setProjectData, setSelectedNode } = useProjectStore();
  const { mutate: updateBasicInfo } = useUpdateBasicInfo(selectedNode?._key ?? '');

  const handleThemeChange = useCallback(
    (data: CustomizationData) => {
      if (!selectedNode || !projectData) return;

      const theme: ThemeConfig = {
        iconColor: data.iconColor,
        cardColor: data.cardColor,
        navbarColor: data.navbarColor,
        leftSidebarColor: data.leftSidebarColor ?? '#f9f9f9',
        rightSidebarColor: data.rightSidebarColor ?? '#f9f9f9',
        backgroundColor: data.backgroundColor ?? '#f9f9f9',
        textColor: data.textColor,
      };

      const updatedTree = updateNodeInTree(projectData, selectedNode._key, (node) => ({
        ...node,
        theme_config: theme,
      }));

      setProjectData(updatedTree);
      setSelectedNode({ ...selectedNode, theme_config: theme } as AnyNodeTree);
    },
    [projectData, selectedNode, setProjectData, setSelectedNode]
  );

  const handleBasicInfoChange = useCallback(
    (data: BasicInfoData) => {
      if (!selectedNode || !projectData) return;

      const nextIcon = data.icon || getIcons(selectedNode?.node_type ?? 'project');

      const shouldUpdate =
        selectedNode?.name !== data.name ||
        (selectedNode?.description ?? '') !== (data.description ?? '') ||
        (selectedNode.icon ?? '') !== (nextIcon ?? '');

      if (!shouldUpdate) return;

      const updates = {
        name: data.name,
        description: data.description ?? '',
        icon: nextIcon,
      };

      // API call
      updateBasicInfo(updates);

      // Optimistic update
      const updatedTree = updateNodeInTree(projectData, selectedNode._key, (node) => ({
        ...node,
        ...updates,
      }));

      setProjectData(updatedTree);
      setSelectedNode({ ...selectedNode, ...updates } as AnyNodeTree);
    },
    [projectData, selectedNode, setProjectData, updateBasicInfo, setSelectedNode]
  );

  return {
    handleThemeChange,
    handleBasicInfoChange,
  };
}
```

---

## Simplified `RightSidebar/index.tsx`

```typescript
import React from 'react';
import { ChevronRight } from 'lucide-react';
import { ResizableHandle, ResizablePanelGroup, Panel as ResizablePanel } from 'react-resizable-panels';
import ConfigSidebarContent from './components/SidebarTabs';
import { BottomTabs } from './components/BottomTabs';
import { useNodeUpdates } from './hooks/useNodeUpdates';
import { useSidebarProps } from './hooks/useSidebarProps';

interface RightSidebarProps {
  className?: string;
  onToggle?: () => void;
}

export const RightSidebar: React.FC<RightSidebarProps> = ({ className, onToggle }) => {
  const { handleThemeChange, handleBasicInfoChange } = useNodeUpdates();
  const sidebarProps = useSidebarProps({ 
    onChangeBasicInfo: handleBasicInfoChange, 
    onChangeTheme: handleThemeChange 
  });

  return (
    <aside className={`relative h-full w-full bg-[var(--right-sidebar-color)] border-l shadow-sm flex flex-col ${className ?? ''}`}>
      {onToggle && (
        <button
          onClick={onToggle}
          aria-label="Hide right sidebar"
          className="absolute group-hover:flex hidden -left-3 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent"
        >
          <ChevronRight className="size-4" />
        </button>
      )}

      <ResizablePanelGroup direction="vertical" className="h-full min-h-0">
        {/* Top: Config */}
        <ResizablePanel collapsible defaultSize={65} minSize={35}>
          <div className="h-full min-h-0 overflow-auto">
            <ConfigSidebarContent {...sidebarProps} />
          </div>
        </ResizablePanel>

        <ResizableHandle className="h-px bg-border shrink-0 border-t-2" withHandle />

        {/* Bottom: Tabs */}
        <ResizablePanel collapsible defaultSize={35} minSize={20}>
          <BottomTabs />
        </ResizablePanel>
      </ResizablePanelGroup>
    </aside>
  );
};
```

---

## Verification

- [ ] Theme changes still apply
- [ ] Basic info updates still work
- [ ] RightSidebar is now ~50 lines

---

## Next Step

👉 [step-02-top-section.md](./step-02-top-section.md)

# Step 1: Main Area - Cleanup

## Goal
Clean up the Main component and move utilities out of `Dashboard.tsx`.

---

## Current Issue in `pages/Dashboard.tsx`

The page component has utility functions mixed in:

```typescript
// pages/Dashboard.tsx (lines 14-82)

// ❌ These utilities don't belong in the page component
function containsGroup(node: AnyNodeTree): boolean { ... }
function flattenGroups(node: AnyNodeTree): AnyNodeTree[] { ... }
function extractShortFocusToken(key: string): string { ... }
function findNodeByFocusToken(root, token): AnyNodeTree | null { ... }

const Dashboard = () => {
  // Effects using these utilities...
};
```

---

## What to Create

### NEW: `features/Dashboard/utils/treeUtils.ts`

```typescript
import type { AnyNodeTree, ProjectNodeTree } from '@/types/project';

/**
 * Check if any Group node exists in tree
 */
export function containsGroup(node: AnyNodeTree): boolean {
  if (node.node_type === 'group') return true;
  const children = (node as { children?: AnyNodeTree[] }).children ?? [];
  return children.some(containsGroup);
}

/**
 * Flatten Group nodes by lifting their children
 */
export function flattenGroups(node: AnyNodeTree): AnyNodeTree[] {
  if (node.node_type === 'group') {
    const children = (node as { children?: AnyNodeTree[] }).children ?? [];
    return children.flatMap(flattenGroups);
  }
  
  const clone = { ...node } as AnyNodeTree;
  const children = (node as { children?: AnyNodeTree[] }).children ?? [];
  
  if (children.length > 0) {
    (clone as { children?: AnyNodeTree[] }).children = children.flatMap(flattenGroups);
  }
  
  return [clone];
}

/**
 * Extract short focus token from node key
 */
export function extractShortFocusToken(key: string): string {
  const uuidRegex = /([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})/;
  const match = key.match(uuidRegex);
  return match ? match[4] : key.slice(0, 6);
}

/**
 * Find node by focus token
 */
export function findNodeByFocusToken(
  root: AnyNodeTree,
  token: string
): AnyNodeTree | null {
  const stack: AnyNodeTree[] = [root];
  
  while (stack.length > 0) {
    const node = stack.pop()!;
    if (extractShortFocusToken(node._key) === token) return node;
    
    const children = (node as { children?: AnyNodeTree[] }).children ?? [];
    stack.push(...children.reverse());
  }
  
  return null;
}
```

---

## Simplified `pages/Dashboard.tsx`

```typescript
import Layout from '@/features/Dashboard/components/Layout';
import SideBar from '@/features/Dashboard/features/Sidebar/components/SideBar';
import Navbar from '@/features/Dashboard/features/Navbar/componets/Navbar';
import MainCanvas from '@/features/Dashboard/features/Main';
import MainWithRightSidebar from '@/features/Dashboard/features/Main/MainWithRightSidebar';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { ResizablePanelGroup } from '@/components/ui/resizable';
import { useGroupFlattening } from '@/features/Dashboard/hooks/useGroupFlattening';
import { useSocketConnection } from '@/services/socket';
import { useEffect } from 'react';

const Dashboard = () => {
  const { selectedNode, projectData, setSelectedNode } = useProjectStore();
  
  // Group flattening (if ?disable=group is set)
  useGroupFlattening();
  
  // Socket connection
  useSocketConnection();
  
  // Default selection
  useEffect(() => {
    if (selectedNode == null && projectData != null) {
      setSelectedNode(projectData);
    }
  }, [selectedNode, projectData, setSelectedNode]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={<MainWithRightSidebar left={<MainCanvas />} />}
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;
```

---

## Optional: Group Flattening Hook

### NEW: `features/Dashboard/hooks/useGroupFlattening.ts`

```typescript
import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import useProjectStore from '../store/useProjectStore';
import { containsGroup, flattenGroups } from '../utils/treeUtils';
import type { ProjectNodeTree } from '@/types/project';

export function useGroupFlattening() {
  const [searchParams] = useSearchParams();
  const { projectData, setProjectData } = useProjectStore();

  useEffect(() => {
    if (!projectData) return;
    
    const disable = searchParams.get('disable');
    const disableGroup = disable?.split(',').includes('group');
    
    if (!disableGroup || !containsGroup(projectData)) return;
    
    const flattened = flattenGroups(projectData);
    const newRoot = flattened[0] as ProjectNodeTree;
    
    if (newRoot?.node_type === 'project') {
      setProjectData(newRoot);
    }
  }, [projectData, searchParams, setProjectData]);
}
```

---

## Verification

- [ ] Dashboard.tsx is now ~30 lines
- [ ] Group flattening still works with `?disable=group`
- [ ] Socket still connects

---

## Next Step

👉 [../right-sidebar/step-01-split-handlers.md](../right-sidebar/step-01-split-handlers.md)

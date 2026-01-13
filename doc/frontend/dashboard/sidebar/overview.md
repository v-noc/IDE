# Sidebar & Tree Navigation

## 🎯 Goal

Build a clean, performant tree navigation sidebar.

---

## 📁 File Structure

```
features/Dashboard/features/Sidebar/
├── index.tsx              # Main sidebar component
├── components/
│   ├── TreeView.tsx      # Tree container
│   ├── TreeNode.tsx      # Individual node component
│   ├── NodeIcon.tsx      # Icon by node type
│   ├── NodeActions.tsx   # Context menu actions
│   └── SearchFilter.tsx  # Filter/search input
├── hooks/
│   └── useTreeNavigation.ts
└── utils/
    └── treeUtils.ts      # Flatten, filter, search
```

---

## 🌳 Tree Data Flow

```
┌─────────────────────────────────────────────────────────┐
│               useProjectTree(projectKey)                │
│         (TanStack Query fetches project tree)           │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│              useProjectStore.projectData                │
│           (Zustand stores tree for navigation)          │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                     <TreeView />                        │
│   Uses expandedNodeIds from store to render tree        │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                     <TreeNode />                        │
│         onClick → setSelectedNode(node)                 │
│         onExpand → toggleNodeExpansion(nodeId)          │
└─────────────────────────────────────────────────────────┘
```

---

## 🧩 Components

### TreeView Container

```typescript
// components/TreeView.tsx
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { TreeNode } from './TreeNode';
import { SearchFilter } from './SearchFilter';
import { useState, useMemo } from 'react';
import { filterTree } from '../utils/treeUtils';

export function TreeView() {
  const projectData = useProjectStore((s) => s.projectData);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Filter tree based on search
  const filteredChildren = useMemo(() => {
    if (!projectData?.children) return [];
    if (!searchQuery) return projectData.children;
    return filterTree(projectData.children, searchQuery);
  }, [projectData?.children, searchQuery]);
  
  if (!projectData) {
    return <EmptyTree />;
  }
  
  return (
    <div className="tree-view">
      <SearchFilter 
        value={searchQuery} 
        onChange={setSearchQuery}
        placeholder="Search files..."
      />
      
      <div className="tree-nodes">
        {filteredChildren.map((node) => (
          <TreeNode 
            key={node._key} 
            node={node} 
            depth={0}
          />
        ))}
      </div>
    </div>
  );
}
```

### TreeNode Component

```typescript
// components/TreeNode.tsx
import { memo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { NodeIcon } from './NodeIcon';
import { ChevronRight, ChevronDown } from 'lucide-react';
import type { AnyNodeTree } from '@/types/project';

interface TreeNodeProps {
  node: AnyNodeTree;
  depth: number;
}

export const TreeNode = memo(function TreeNode({ 
  node, 
  depth 
}: TreeNodeProps) {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  
  const isSelected = selectedNode?._key === node._key;
  const isExpanded = expandedNodeIds.includes(node._key);
  const hasChildren = 'children' in node && node.children?.length > 0;
  
  const handleClick = () => {
    setSelectedNode(node);
  };
  
  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node._key);
  };
  
  return (
    <div className="tree-node-container">
      <div
        className={`tree-node ${isSelected ? 'selected' : ''}`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
        onClick={handleClick}
      >
        {/* Expand/Collapse Arrow */}
        <button 
          className="tree-node-toggle"
          onClick={handleToggle}
          disabled={!hasChildren}
        >
          {hasChildren && (
            isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />
          )}
        </button>
        
        {/* Icon */}
        <NodeIcon nodeType={node.node_type} />
        
        {/* Name */}
        <span className="tree-node-name">{node.name}</span>
      </div>
      
      {/* Children (if expanded) */}
      {isExpanded && hasChildren && (
        <div className="tree-node-children">
          {node.children.map((child) => (
            <TreeNode 
              key={child._key} 
              node={child} 
              depth={depth + 1} 
            />
          ))}
        </div>
      )}
    </div>
  );
});
```

---

## ⚡ Performance: Virtualization

For large trees, use virtualization:

```typescript
// components/TreeView.tsx (virtualized version)
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef, useMemo } from 'react';
import { flattenTree } from '../utils/treeUtils';

export function VirtualizedTreeView() {
  const parentRef = useRef<HTMLDivElement>(null);
  const projectData = useProjectStore((s) => s.projectData);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  
  // Flatten tree to array for virtualization
  const flatNodes = useMemo(() => {
    if (!projectData?.children) return [];
    return flattenTree(projectData.children, expandedNodeIds);
  }, [projectData?.children, expandedNodeIds]);
  
  const virtualizer = useVirtualizer({
    count: flatNodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 32, // Estimated row height
    overscan: 10,
  });
  
  return (
    <div ref={parentRef} className="tree-view-scroll">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const { node, depth } = flatNodes[virtualItem.index];
          return (
            <div
              key={node._key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <TreeNodeRow node={node} depth={depth} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

---

## 🔧 Tree Utilities

```typescript
// utils/treeUtils.ts
import type { AnyNodeTree } from '@/types/project';

interface FlatNode {
  node: AnyNodeTree;
  depth: number;
}

// Flatten tree for virtualization
export function flattenTree(
  nodes: AnyNodeTree[],
  expandedIds: string[],
  depth = 0
): FlatNode[] {
  const result: FlatNode[] = [];
  
  for (const node of nodes) {
    result.push({ node, depth });
    
    if (
      'children' in node &&
      node.children?.length > 0 &&
      expandedIds.includes(node._key)
    ) {
      result.push(...flattenTree(node.children, expandedIds, depth + 1));
    }
  }
  
  return result;
}

// Filter tree by search query
export function filterTree(
  nodes: AnyNodeTree[],
  query: string
): AnyNodeTree[] {
  const lowerQuery = query.toLowerCase();
  
  return nodes.filter((node) => {
    const nameMatch = node.name.toLowerCase().includes(lowerQuery);
    
    if ('children' in node && node.children?.length > 0) {
      const filteredChildren = filterTree(node.children, query);
      if (filteredChildren.length > 0) {
        return true; // Include parent if any child matches
      }
    }
    
    return nameMatch;
  });
}

// Find node by key in tree
export function findNodeByKey(
  node: AnyNodeTree,
  key: string
): AnyNodeTree | null {
  if (node._key === key) return node;
  
  if ('children' in node && node.children) {
    for (const child of node.children) {
      const found = findNodeByKey(child, key);
      if (found) return found;
    }
  }
  
  return null;
}
```

---

## 📖 Next Steps

- **[../canvas/](../canvas/)** - Canvas/graph visualization

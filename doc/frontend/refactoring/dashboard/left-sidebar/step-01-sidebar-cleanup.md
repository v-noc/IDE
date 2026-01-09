# Step 1: Left Sidebar - Cleanup SideBar.tsx

## Goal
Simplify `SideBar.tsx` by extracting logic into hooks.

## Current Files

```
Sidebar/components/
├── SideBar.tsx           # Main component (~170 lines)
├── ProjectTree.tsx       # Tree rendering
├── SelectNodeDialog.tsx  # Node selection modal
├── TreeNode/            # Node components
└── VirtualFolders/      # Virtual folder feature
```

---

## What to Refactor in SideBar.tsx

The component likely has:
- Tree filtering logic
- Expansion state management
- Search functionality
- Event handlers

Let's extract into focused hooks.

---

## NEW: `Sidebar/hooks/useTreeFilter.ts`

```typescript
import { useMemo, useState } from 'react';
import type { AnyNodeTree } from '@/types/project';

function filterTree(nodes: AnyNodeTree[], query: string): AnyNodeTree[] {
  if (!query.trim()) return nodes;
  
  const lowerQuery = query.toLowerCase();
  
  return nodes.reduce<AnyNodeTree[]>((acc, node) => {
    const nameMatch = node.name.toLowerCase().includes(lowerQuery);
    
    const children = 'children' in node ? node.children as AnyNodeTree[] : [];
    const filteredChildren = filterTree(children, query);
    
    if (nameMatch || filteredChildren.length > 0) {
      acc.push({
        ...node,
        children: filteredChildren,
      } as AnyNodeTree);
    }
    
    return acc;
  }, []);
}

export function useTreeFilter(nodes: AnyNodeTree[] | undefined) {
  const [searchQuery, setSearchQuery] = useState('');
  
  const filteredNodes = useMemo(() => {
    if (!nodes) return [];
    if (!searchQuery.trim()) return nodes;
    return filterTree(nodes, searchQuery);
  }, [nodes, searchQuery]);
  
  return {
    searchQuery,
    setSearchQuery,
    filteredNodes,
    isFiltering: searchQuery.trim().length > 0,
  };
}
```

---

## Simplified SideBar.tsx Structure

```typescript
// Sidebar/components/SideBar.tsx
import { useTreeFilter } from '../hooks/useTreeFilter';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { ProjectTree } from './ProjectTree';
import { SearchInput } from './SearchInput';

export default function SideBar() {
  const projectData = useProjectStore((s) => s.projectData);
  const { searchQuery, setSearchQuery, filteredNodes } = useTreeFilter(
    projectData?.children
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header with search */}
      <div className="p-3 border-b">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search..."
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-auto">
        <ProjectTree nodes={filteredNodes} />
      </div>
    </div>
  );
}
```

---

## NEW: `Sidebar/components/SearchInput.tsx`

```typescript
import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function SearchInput({ value, onChange, placeholder }: SearchInputProps) {
  return (
    <div className="relative">
      <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pl-8 pr-8"
      />
      {value && (
        <button
          onClick={() => onChange('')}
          className="absolute right-2 top-1/2 -translate-y-1/2"
        >
          <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
        </button>
      )}
    </div>
  );
}
```

---

## Verification

- [ ] Search still filters tree
- [ ] Tree still renders correctly
- [ ] Expansion still works

---

## Next Step

👉 [step-02-tree-node.md](./step-02-tree-node.md)

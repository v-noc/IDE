# React 19 Best Practices

## 🎯 Goal

Leverage React 19's new features for cleaner, faster code.

---

## ⚡ Key React 19 Features

### 1. Automatic Batching (Already Active)

React 19 automatically batches state updates, even in:
- Event handlers
- Timeouts
- Promises
- Native event handlers

```typescript
// React 19 batches these automatically
async function handleClick() {
  setLoading(true);
  await saveData();
  setLoading(false);
  setSuccess(true);
  // Only ONE re-render!
}
```

---

### 2. Concurrent Features

#### Transitions

Use for non-urgent updates (like filtering):

```typescript
import { useTransition } from 'react';

function TreeFilter() {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();
  
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Immediately update the input
    setQuery(e.target.value);
    
    // Defer the expensive filter
    startTransition(() => {
      setFilteredNodes(filterTree(nodes, e.target.value));
    });
  };
  
  return (
    <>
      <input value={query} onChange={handleSearch} />
      {isPending && <Spinner />}
      <TreeView nodes={filteredNodes} />
    </>
  );
}
```

#### Deferred Values

For expensive computations:

```typescript
import { useDeferredValue } from 'react';

function SearchResults({ query }: { query: string }) {
  // React will keep showing old results while computing new ones
  const deferredQuery = useDeferredValue(query);
  
  const results = useMemo(
    () => expensiveSearch(deferredQuery),
    [deferredQuery]
  );
  
  return <ResultsList results={results} />;
}
```

---

### 3. Suspense for Data Fetching

#### With TanStack Query

```typescript
import { useSuspenseQuery } from '@tanstack/react-query';
import { Suspense } from 'react';

// Component using suspense query
function ProjectTree({ projectId }: { projectId: string }) {
  const { data } = useSuspenseQuery({
    queryKey: ['project', projectId],
    queryFn: () => fetchProject(projectId),
  });
  
  // data is guaranteed to exist - no loading checks!
  return <Tree nodes={data.children} />;
}

// Parent with Suspense boundary
function DashboardPage() {
  return (
    <Suspense fallback={<TreeSkeleton />}>
      <ProjectTree projectId={projectId} />
    </Suspense>
  );
}
```

---

### 4. Server Components Prep

Even though you're using Vite (client), structure code for future server compatibility:

```typescript
// ✅ Keep server-fetching logic separate
// services/projects/api.ts
export const projectsApi = {
  getTree: (id: string) => fetch(`/api/projects/${id}`).then(r => r.json()),
};

// ✅ Wrap in client hook
// services/projects/queries.ts
'use client'; // Future-proofing
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from './api';

export const useProjectTree = (id: string) => {
  return useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.getTree(id),
  });
};
```

---

## 🎣 Hook Best Practices

### Custom Hook Naming

```typescript
// ✅ Action-oriented names
useNodeSelection()     // Not: useNodeSelectionStore
useProjectNavigation() // Not: useProjectNav
useCodeEditor()        // Not: useCode
```

### Hook Composition

```typescript
// Build complex hooks from simple ones
function useDashboard(projectId: string) {
  // Combine multiple hooks
  const project = useProjectTree(projectId);
  const selection = useNodeSelection();
  const navigation = useProjectNavigation();
  const socket = useProjectSocket(projectId);
  
  return {
    project,
    selection,
    navigation,
    socket,
    isReady: !project.isLoading,
  };
}
```

---

## 📦 Component Best Practices

### Prefer Composition

```typescript
// ❌ Too many props
<Button
  variant="primary"
  size="lg"
  icon={<Save />}
  iconPosition="left"
  loading={isSaving}
  disabled={!isDirty}
  onClick={handleSave}
/>

// ✅ Composition
<Button variant="primary" size="lg" onClick={handleSave} disabled={!isDirty}>
  {isSaving ? <Spinner /> : <Save />}
  Save Changes
</Button>
```

### Use React.memo Wisely

```typescript
// ✅ Memo for list items
const TreeNode = memo(function TreeNode({ node, depth }) {
  // ...
});

// ❌ Don't memo everything - React is already fast
// Only memo when you see actual performance issues
```

### Early Returns

```typescript
// ✅ Clean early returns
function NodeCard({ nodeId }: { nodeId: string }) {
  const { data, isLoading, error } = useNode(nodeId);
  
  if (isLoading) return <Skeleton />;
  if (error) return <ErrorCard error={error} />;
  if (!data) return null;
  
  // Main render - data is guaranteed
  return <Card>{data.name}</Card>;
}
```

---

## 📖 Summary

| Feature | When to Use |
|---------|-------------|
| `useTransition` | Non-urgent updates (filters, search) |
| `useDeferredValue` | Expensive computations |
| `Suspense` | Data loading states |
| `memo` | List items, expensive components |
| Custom Hooks | Reusable stateful logic |

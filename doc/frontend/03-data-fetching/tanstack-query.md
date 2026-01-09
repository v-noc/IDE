# TanStack Query Best Practices

## 🎯 Goal

Master data fetching with TanStack Query (React Query) for React 19.

---

## 📐 Query Key Factory Pattern

### Problem: Inconsistent Query Keys

```typescript
// ❌ BAD: Keys scattered everywhere, easy to mismatch
useQuery({ queryKey: ['project', projectId] });
useQuery({ queryKey: ['projects', projectId] }); // Typo! Different cache
```

### Solution: Centralized Key Factory

```typescript
// services/queryKeys.ts
export const queryKeys = {
  // Projects
  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    list: (filters: string) => [...queryKeys.projects.lists(), filters] as const,
    details: () => [...queryKeys.projects.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
    tree: (id: string) => [...queryKeys.projects.detail(id), 'tree'] as const,
  },
  
  // Code
  code: {
    all: ['code'] as const,
    detail: (elementId: string) => [...queryKeys.code.all, elementId] as const,
  },
  
  // Logs
  logs: {
    all: ['logs'] as const,
    tree: (nodeId: string) => [...queryKeys.logs.all, 'tree', nodeId] as const,
  },
  
  // Nodes
  nodes: {
    all: ['nodes'] as const,
    detail: (nodeId: string) => [...queryKeys.nodes.all, nodeId] as const,
  },
};
```

### Usage

```typescript
// ✅ GOOD: Consistent keys everywhere
import { queryKeys } from '@/services/queryKeys';

// In query
useQuery({
  queryKey: queryKeys.projects.tree(projectId),
  queryFn: () => fetchProjectTree(projectId),
});

// In invalidation
queryClient.invalidateQueries({
  queryKey: queryKeys.projects.detail(projectId),
});

// Invalidate all projects
queryClient.invalidateQueries({
  queryKey: queryKeys.projects.all,
});
```

---

## 🏗️ Query Hook Organization

### File Structure

```
services/
├── queryKeys.ts              # Centralized keys
├── projects/
│   ├── api.ts               # Raw API functions
│   ├── queries.ts           # useQuery hooks
│   └── mutations.ts         # useMutation hooks
├── code/
│   ├── api.ts
│   ├── queries.ts
│   └── mutations.ts
└── logs/
    ├── api.ts
    └── queries.ts
```

### Example: Projects Service

```typescript
// services/projects/api.ts
import { api } from '@/lib/api';
import type { ProjectNode, ProjectNodeTree } from '@/types/project';

export const projectsApi = {
  getAll: (): Promise<ProjectNode[]> => 
    api('/projects'),
  
  getTree: (projectId: string): Promise<ProjectNodeTree> =>
    api(`/projects/${projectId}`),
  
  create: (data: { name: string; path: string; description: string }) =>
    api('/projects', { method: 'POST', body: data }),
  
  delete: (projectId: string) =>
    api(`/projects/${projectId}`, { method: 'DELETE' }),
};
```

```typescript
// services/projects/queries.ts
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';
import { projectsApi } from './api';

export const useProjects = () => {
  return useQuery({
    queryKey: queryKeys.projects.lists(),
    queryFn: projectsApi.getAll,
  });
};

export const useProjectTree = (projectId: string) => {
  return useQuery({
    queryKey: queryKeys.projects.tree(projectId),
    queryFn: () => projectsApi.getTree(projectId),
    enabled: !!projectId,
  });
};
```

```typescript
// services/projects/mutations.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';
import { projectsApi } from './api';

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.lists(),
      });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.all,
      });
    },
  });
};
```

---

## ⚡ React 19 + TanStack Query

### Use Suspense Mode

```typescript
// Enable suspense in query
export const useProjectTree = (projectId: string) => {
  return useSuspenseQuery({
    queryKey: queryKeys.projects.tree(projectId),
    queryFn: () => projectsApi.getTree(projectId),
  });
};

// In component - no loading state needed!
function ProjectView({ projectId }: { projectId: string }) {
  const { data: project } = useProjectTree(projectId);
  
  // data is guaranteed to exist
  return <div>{project.name}</div>;
}

// Wrap with Suspense boundary
function ProjectPage({ projectId }: { projectId: string }) {
  return (
    <Suspense fallback={<ProjectSkeleton />}>
      <ProjectView projectId={projectId} />
    </Suspense>
  );
}
```

### Error Boundaries

```typescript
// components/ErrorBoundary.tsx
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div role="alert">
      <p>Something went wrong:</p>
      <pre>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
}

// Usage
<ErrorBoundary FallbackComponent={ErrorFallback}>
  <Suspense fallback={<Loading />}>
    <ProjectView projectId={projectId} />
  </Suspense>
</ErrorBoundary>
```

---

## 🔄 Optimistic Updates

```typescript
export const useUpdateNode = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ nodeId, data }) => api(`/nodes/${nodeId}`, {
      method: 'PATCH',
      body: data,
    }),
    
    // Optimistic update
    onMutate: async ({ nodeId, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({
        queryKey: queryKeys.nodes.detail(nodeId),
      });
      
      // Snapshot previous value
      const previousNode = queryClient.getQueryData(
        queryKeys.nodes.detail(nodeId)
      );
      
      // Optimistically update
      queryClient.setQueryData(
        queryKeys.nodes.detail(nodeId),
        (old) => ({ ...old, ...data })
      );
      
      return { previousNode };
    },
    
    // Rollback on error
    onError: (err, { nodeId }, context) => {
      queryClient.setQueryData(
        queryKeys.nodes.detail(nodeId),
        context?.previousNode
      );
    },
    
    // Refetch after success or error
    onSettled: (_, __, { nodeId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.nodes.detail(nodeId),
      });
    },
  });
};
```

---

## 📖 Next Steps

- **[../04-socket-realtime/socket-integration.md](../04-socket-realtime/socket-integration.md)** - Real-time data sync

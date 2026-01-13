# Step 1: Create Centralized Query Keys

## Goal
Create a single source of truth for all TanStack Query cache keys.

## Why
Your code fetching is scattered across multiple files with inconsistent keys:
- `["projectTree", key]` in `useProject.tsx`
- `["code", elementId]` in `useCodeElement.ts`
- `["functionLogTree", functionId]` in `useLogs.ts`

This makes cache invalidation error-prone and hard to maintain.

---

## What to Create

### New File: `src/frontend/src/lib/queryKeys.ts`

```typescript
/**
 * Centralized query keys for TanStack Query.
 * All query keys should be defined here for consistency.
 */
export const queryKeys = {
  // Projects
  projects: {
    all: ['projects'] as const,
    list: () => [...queryKeys.projects.all, 'list'] as const,
    detail: (id: string) => [...queryKeys.projects.all, 'detail', id] as const,
    tree: (id: string) => [...queryKeys.projects.all, 'tree', id] as const,
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

  // Groups
  groups: {
    all: ['groups'] as const,
    list: (projectKey: string) => [...queryKeys.groups.all, 'list', projectKey] as const,
  },

  // Documents
  documents: {
    all: ['documents'] as const,
    list: (nodeKey: string) => [...queryKeys.documents.all, 'list', nodeKey] as const,
    detail: (docId: string) => [...queryKeys.documents.all, 'detail', docId] as const,
  },
} as const;
```

---

## How to Use

After creating this file, you'll update existing query hooks in later steps:

```typescript
// Before
useQuery({ queryKey: ["projectTree", key], ... });

// After
import { queryKeys } from '@/lib/queryKeys';
useQuery({ queryKey: queryKeys.projects.tree(key), ... });
```

---

## Verification

- [ ] File created at `src/frontend/src/lib/queryKeys.ts`
- [ ] No TypeScript errors
- [ ] App still runs (`npm run dev`)

---

## Next Step

👉 [Step 2: Unify Code Service](./step-02-code-service.md)

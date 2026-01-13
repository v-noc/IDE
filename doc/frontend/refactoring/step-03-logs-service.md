# Step 3: Unify Logs Service

## Goal
Create ONE place for all logs fetching that Canvas nodes, Logs Sidebar, and Right Panel all use.

## Why
Currently logs are fetched in:
- `features/Dashboard/features/Main/service/useLogs.ts`

Let's move it to a centralized location and connect it to the query keys.

---

## What to Create

### Folder Structure
```
src/frontend/src/services/
├── logs/
│   ├── index.ts       # Public exports
│   ├── api.ts         # Raw API functions
│   └── queries.ts     # useQuery hooks
```

---

### File 1: `src/frontend/src/services/logs/api.ts`

```typescript
import { api } from '@/lib/api';
import API_ROUTES from '@/lib/apiRoutes';

export interface LogNode {
  id: string;
  created_at: string;
  timestamp: string;
  event_type: string;
  message: string;
  duration_ms: number | null;
  chain_id: string | null;
  payload: Record<string, unknown> | null;
  result: unknown | null;
  error: Record<string, unknown> | null;
  level_name: string | null;
}

export interface LogTreeNode extends LogNode {
  children: LogTreeNode[];
}

export const logsApi = {
  getLogTree: (nodeId: string): Promise<LogTreeNode[]> =>
    api(`${API_ROUTES.LOGS}${nodeId}/tree`),
};
```

---

### File 2: `src/frontend/src/services/logs/queries.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryKeys';
import { logsApi, type LogTreeNode } from './api';

/**
 * Fetch log tree for any node.
 * Used by: Canvas nodes, Logs Sidebar, Right Panel
 */
export const useLogTree = (nodeId: string | undefined) => {
  return useQuery<LogTreeNode[]>({
    queryKey: queryKeys.logs.tree(nodeId ?? ''),
    queryFn: () => logsApi.getLogTree(nodeId!),
    enabled: !!nodeId,
    staleTime: 30 * 1000, // 30 seconds (logs update frequently)
  });
};
```

---

### File 3: `src/frontend/src/services/logs/index.ts`

```typescript
export { useLogTree } from './queries';
export type { LogNode, LogTreeNode } from './api';
```

---

## Update Existing Code

### In `RightSidebar/components/sections/LogsSection.tsx`

```diff
- import { useFunctionLogTree, useCallLogTree } from '../../../service/useLogs';
+ import { useLogTree } from '@/services/logs';

function LogsSection({ nodeId, nodeType }) {
- const { data: logs } = nodeType === 'call' 
-   ? useCallLogTree(nodeId) 
-   : useFunctionLogTree(nodeId);
+ const { data: logs } = useLogTree(nodeId);
  // ...
}
```

---

## What to Delete (After Migration)

- `features/Dashboard/features/Main/service/useLogs.ts`

---

## Verification

- [ ] Logs sidebar still shows logs
- [ ] Log details still expand correctly
- [ ] No TypeScript errors

---

## Next Step

👉 [Step 4: Create Socket Provider](./step-04-socket-provider.md)

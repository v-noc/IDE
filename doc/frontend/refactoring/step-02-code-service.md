# Step 2: Unify Code Service

## Goal
Create ONE place for all code-related data fetching that Canvas nodes, Code Editor, and Right Panel all use.

## Why
Currently code is fetched in multiple places:
- `features/Dashboard/features/Main/service/useCodeElement.ts`
- `features/Dashboard/features/Main/service/useCodeElement.tsx`
- `features/Dashboard/features/Main/components/Code/useEditorCode.ts`
- `features/Dashboard/features/Main/components/Code/useEditableCode.ts`

This causes duplicate fetches and out-of-sync data.

---

## What to Create

### New Folder Structure
```
src/frontend/src/services/
├── code/
│   ├── index.ts       # Public exports
│   ├── api.ts         # Raw API functions
│   ├── queries.ts     # useQuery hooks
│   └── mutations.ts   # useMutation hooks
```

---

### File 1: `src/frontend/src/services/code/api.ts`

```typescript
import { api } from '@/lib/api';
import API_ROUTES from '@/lib/apiRoutes';

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  code: string;
}

export const codeApi = {
  getCode: (elementId: string): Promise<CodeData> =>
    api(`${API_ROUTES.CODE_ELEMENTS}${elementId}/code`),

  writeCode: (elementId: string, code: string): Promise<void> =>
    api(`${API_ROUTES.CODE_ELEMENTS}${elementId}/write-code`, {
      method: 'POST',
      body: { code },
    }),
};
```

---

### File 2: `src/frontend/src/services/code/queries.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryKeys';
import { codeApi, type CodeData } from './api';

/**
 * Fetch code for any node.
 * Used by: Canvas nodes, Code Editor, Right Panel
 * All consumers share the same cache!
 */
export const useCode = (elementId: string | undefined) => {
  return useQuery<CodeData>({
    queryKey: queryKeys.code.detail(elementId ?? ''),
    queryFn: () => codeApi.getCode(elementId!),
    enabled: !!elementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
```

---

### File 3: `src/frontend/src/services/code/mutations.ts`

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryKeys';
import { codeApi } from './api';

/**
 * Write code mutation.
 * Automatically invalidates the cache so all consumers update.
 */
export const useWriteCode = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ elementId, code }: { elementId: string; code: string }) =>
      codeApi.writeCode(elementId, code),

    onSuccess: (_, { elementId }) => {
      // All components using useCode(elementId) will refetch
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(elementId),
      });
    },
  });
};
```

---

### File 4: `src/frontend/src/services/code/index.ts`

```typescript
// Public API
export { useCode } from './queries';
export { useWriteCode } from './mutations';
export type { CodeData } from './api';
```

---

## Update Existing Code

### In `Code/index.tsx` (Main Code Editor)

```diff
- import { useGetCodeForNode, useWriteCode } from '../service/useCodeElement';
+ import { useCode, useWriteCode } from '@/services/code';

function Code() {
  const selectedNode = useProjectStore((s) => s.selectedNode);
- const { data: codeData } = useGetCodeForNode(selectedNode?._key);
+ const { data: codeData } = useCode(selectedNode?._key);
  const { mutate: writeCode } = useWriteCode();
  // ...
}
```

### In `Canvas/components/EnhancedNode.tsx`

```diff
- import { useEditorCode } from '@/features/Dashboard/features/Main/components/Code/useEditorCode';
+ import { useCode, useWriteCode } from '@/services/code';

const EnhancedNode = ({ data }) => {
- const { data: codeData } = useEditorCode(showCode ? effectiveNodeId : undefined);
+ const { data: codeData } = useCode(showCode ? effectiveNodeId : undefined);
+ const { mutate: writeCode, isPending } = useWriteCode();
  // ...
}
```

---

## What to Delete (After Migration)

Once everything is updated, you can delete:
- `features/Dashboard/features/Main/service/useCodeElement.ts`
- `features/Dashboard/features/Main/service/useCodeElement.tsx`
- `features/Dashboard/features/Main/components/Code/useEditorCode.ts`

Keep `useEditableCode.ts` but simplify it to just handle local editing state.

---

## Verification

- [ ] New services folder created
- [ ] Code Editor still works
- [ ] Canvas nodes still show code
- [ ] Saving code in Editor updates Canvas (shared cache!)

---

## Next Step

👉 [Step 3: Unify Logs Service](./step-03-logs-service.md)

# Step 5: Connect Socket to React Query

## Goal
When the backend sends socket events, automatically update the React Query cache.

## Why
Right now you use `window.dispatchEvent` to notify components:
```typescript
// In useCodeElement.ts
window.dispatchEvent(new CustomEvent('code-saved'));
```

This is fragile. Instead, we'll have socket events directly invalidate the query cache.

---

## What to Create

### NEW: `src/frontend/src/services/socket/useSocketSync.ts`

```typescript
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/queryKeys';
import { useSocketContext } from './SocketProvider';

/**
 * Syncs socket events to React Query cache.
 * Call this once at app level (e.g., in Dashboard layout).
 */
export function useSocketSync() {
  const { socket, isConnected } = useSocketContext();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!socket || !isConnected) return;

    // When code is updated (from backend processing or another user)
    const onCodeUpdated = (data: { element_id: string }) => {
      console.log('🔄 Code updated:', data.element_id);
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(data.element_id),
      });
    };

    // When new logs are created
    const onLogsNew = (data: { node_id: string }) => {
      console.log('🔄 New logs:', data.node_id);
      queryClient.invalidateQueries({
        queryKey: queryKeys.logs.tree(data.node_id),
      });
    };

    // When project structure changes
    const onProjectUpdated = (data: { project_id: string }) => {
      console.log('🔄 Project updated:', data.project_id);
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.tree(data.project_id),
      });
    };

    // Subscribe to events
    socket.on('code:updated', onCodeUpdated);
    socket.on('logs:new', onLogsNew);
    socket.on('project:updated', onProjectUpdated);

    return () => {
      socket.off('code:updated', onCodeUpdated);
      socket.off('logs:new', onLogsNew);
      socket.off('project:updated', onProjectUpdated);
    };
  }, [socket, isConnected, queryClient]);
}
```

---

## Update Socket Index

```diff
// src/frontend/src/services/socket/index.ts
export { SocketProvider, useSocketContext } from './SocketProvider';
export { useSocket, useProjectRoom } from './hooks';
+ export { useSocketSync } from './useSocketSync';
export { getSocket, disconnectSocket } from './socket';
```

---

## Use in Dashboard

### In `features/Dashboard/components/Layout.tsx` or main Dashboard component

```diff
+ import { useSocketSync, useProjectRoom } from '@/services/socket';
+ import { useParams } from 'react-router-dom';

function DashboardLayout({ children }) {
+ const { projectKey } = useParams();
+ 
+ // Subscribe to socket events
+ useSocketSync();
+ useProjectRoom(projectKey);

  return (
    <div className="dashboard-layout">
      {/* ... */}
    </div>
  );
}
```

---

## Remove window.dispatchEvent

Now you can remove the custom event dispatch:

### In `services/code/mutations.ts`

```diff
export const useWriteCode = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ elementId, code }) => codeApi.writeCode(elementId, code),
    onSuccess: (_, { elementId }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(elementId),
      });
-     // No longer needed!
-     window.dispatchEvent(new CustomEvent('code-saved'));
    },
  });
};
```

---

## Backend Note

Make sure your backend emits these events. In `manager.py`:

```python
# After code is saved
await socket_manager.emit_to_project(
    project_id, 
    'code:updated', 
    {'element_id': element_id}
)

# After new logs are created
await socket_manager.emit_to_project(
    project_id,
    'logs:new',
    {'node_id': node_id}
)
```

---

## Verification

- [ ] Console shows "🔄 Code updated" when backend processes
- [ ] Canvas nodes update when code is saved elsewhere
- [ ] Logs sidebar updates when new logs arrive

---

## Next Step

👉 [Step 6: Split EnhancedNode](./step-06-split-enhanced-node.md)

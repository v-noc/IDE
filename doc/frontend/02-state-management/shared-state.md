# Shared State: Code & Logs

## 🎯 Goal

Handle state that's used in multiple places (Code, Logs) cleanly.

---

## 🤔 The Problem

You mentioned:
> "there are some shared state like code and logs, codes are in code tag and in nodes, logs are show in logs sidebar and also will be add on logs also"

This is **cross-feature shared state** - the tricky kind.

---

## ✅ Solution: TanStack Query as Single Source of Truth

Since code and logs come from the **server**, use TanStack Query's cache as the shared state:

```
┌────────────────────────────────────────────────────┐
│                  TanStack Query Cache              │
│    ['code', elementId] → CodeResponse              │
│    ['logs', functionId] → LogTreeNode[]            │
└───────────┬────────────────────────┬───────────────┘
            │                        │
            ▼                        ▼
     ┌──────────────┐       ┌────────────────┐
     │ Code Editor  │       │ Logs Sidebar   │
     │ (Main area)  │       │                │
     └──────────────┘       └────────────────┘
            │                        │
            ▼                        ▼
     ┌──────────────┐       ┌────────────────┐
     │ Code Tag     │       │ Node Log Tab   │
     │ (in nodes)   │       │                │
     └──────────────┘       └────────────────┘
```

Both consumers call the **same query** - TanStack Query handles deduplication and caching.

---

## 💻 Code Sharing Pattern

### 1. Create a Shared Query Hook

```typescript
// services/code/useCode.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  node_type: string;
  qname: string;
  code: string;
}

// Query key factory for consistency
export const codeKeys = {
  all: ['code'] as const,
  detail: (elementId: string) => [...codeKeys.all, elementId] as const,
};

// Fetch hook - used by ANY component needing code
export const useCode = (elementId: string | undefined) => {
  return useQuery({
    queryKey: codeKeys.detail(elementId ?? ''),
    queryFn: () => api<CodeData>(`/code-elements/${elementId}/code`),
    enabled: !!elementId,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
};

// Mutation hook - updates propagate everywhere automatically
export const useWriteCode = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ elementId, code }: { elementId: string; code: string }) =>
      api(`/code-elements/${elementId}/write-code`, {
        method: 'POST',
        body: { code },
      }),
    onSuccess: (_, { elementId }) => {
      // Invalidate cache - all components using this code will refetch
      queryClient.invalidateQueries({
        queryKey: codeKeys.detail(elementId),
      });
    },
  });
};
```

### 2. Use in Multiple Components

```typescript
// features/Dashboard/features/Main/components/Code/CodeEditor.tsx
function CodeEditor({ elementId }: { elementId: string }) {
  const { data: codeData, isLoading } = useCode(elementId);
  const { mutate: writeCode } = useWriteCode();
  
  if (isLoading) return <Skeleton />;
  
  return (
    <MonacoEditor
      value={codeData?.code}
      onSave={(code) => writeCode({ elementId, code })}
    />
  );
}

// features/Dashboard/features/Sidebar/components/CodeTag.tsx  
function CodeTag({ elementId }: { elementId: string }) {
  const { data: codeData } = useCode(elementId);
  
  // Uses SAME cached data - no extra fetch!
  return <code>{codeData?.code?.slice(0, 100)}...</code>;
}
```

---

## 📋 Logs Sharing Pattern

Same approach for logs:

```typescript
// services/logs/useLogs.ts
import { useQuery } from '@tanstack/react-query';

export interface LogNode {
  id: string;
  timestamp: string;
  event_type: string;
  message: string;
  level_name: string | null;
  children: LogNode[];
}

export const logKeys = {
  all: ['logs'] as const,
  tree: (nodeId: string) => [...logKeys.all, 'tree', nodeId] as const,
  function: (functionId: string) => [...logKeys.all, 'function', functionId] as const,
};

export const useLogTree = (nodeId: string | undefined) => {
  return useQuery({
    queryKey: logKeys.tree(nodeId ?? ''),
    queryFn: () => api<LogNode[]>(`/logs/${nodeId}/tree`),
    enabled: !!nodeId,
  });
};
```

---

## 🔔 Real-time Updates with Socket.io

When logs/code update via WebSocket:

```typescript
// In your socket handler
import { useQueryClient } from '@tanstack/react-query';
import { codeKeys } from '@/services/code/useCode';
import { logKeys } from '@/services/logs/useLogs';

function useSocketSync() {
  const queryClient = useQueryClient();
  
  useEffect(() => {
    const socket = getSocket();
    
    // When code changes from backend
    socket?.on('code:updated', (data: { elementId: string }) => {
      queryClient.invalidateQueries({
        queryKey: codeKeys.detail(data.elementId),
      });
    });
    
    // When new logs arrive
    socket?.on('logs:new', (data: { nodeId: string }) => {
      queryClient.invalidateQueries({
        queryKey: logKeys.tree(data.nodeId),
      });
    });
    
    return () => {
      socket?.off('code:updated');
      socket?.off('logs:new');
    };
  }, [queryClient]);
}
```

---

## 🚫 Avoid: Window Event Pattern

Your current code uses:
```typescript
// ❌ Avoid: Tightly couples components
window.dispatchEvent(new CustomEvent('code-saved'));
```

**Why it's problematic:**
- Hard to track what listens to what
- No TypeScript safety
- Can't easily test

**Better:** Use TanStack Query invalidation (shown above).

---

## 📖 Next Steps

- **[../04-socket-realtime/socket-integration.md](../04-socket-realtime/socket-integration.md)** - Full socket.io patterns

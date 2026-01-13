# Code & Logs State Synchronization

## 🎯 Goal

Keep code and logs **in sync** across Canvas nodes, Code Editor, Logs Sidebar, and RightPanel.

---

## 🔄 The Sync Problem

```
User edits code in Code Editor
         │
         ▼
┌─────────────────┐
│  Save to API    │
└────────┬────────┘
         │
         ▼
How do these know to update?
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌───────────┐
│ Canvas │ │ Right  │ │ Logs      │
│  Node  │ │ Panel  │ │ Sidebar   │
└────────┘ └────────┘ └───────────┘
```

---

## ✅ Solution: TanStack Query as Single Source of Truth

### Shared Query Hooks

```typescript
// services/code/useCode.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';

export interface CodeData {
  file_id: string;
  file_name: string;
  file_path: string;
  qname: string;
  code: string;
}

// ✅ Used by Canvas nodes, Code Editor, Right Panel - same cache!
export const useCode = (nodeId: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.code.detail(nodeId ?? ''),
    queryFn: () => api<CodeData>(`/code-elements/${nodeId}/code`),
    enabled: !!nodeId,
    staleTime: 5 * 60 * 1000, // 5 min cache
  });
};

// ✅ Mutation invalidates cache - all consumers auto-update
export const useWriteCode = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ nodeId, code }: { nodeId: string; code: string }) =>
      api(`/code-elements/${nodeId}/write-code`, {
        method: 'POST',
        body: { code },
      }),
    onSuccess: (_, { nodeId }) => {
      // This triggers refetch in ALL components using this code
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(nodeId),
      });
    },
  });
};
```

```typescript
// services/logs/useLogs.ts
export interface LogNode {
  id: string;
  timestamp: string;
  event_type: string;
  message: string;
  level_name: string;
  children: LogNode[];
}

// ✅ Used by Canvas nodes, Logs Sidebar, Right Panel
export const useLogsForNode = (nodeId: string | undefined) => {
  return useQuery({
    queryKey: queryKeys.logs.tree(nodeId ?? ''),
    queryFn: () => api<LogNode[]>(`/logs/${nodeId}/tree`),
    enabled: !!nodeId,
    staleTime: 30 * 1000, // Logs update more frequently
  });
};
```

---

## 🎨 Canvas Node with Shared State

### Before (Current Pattern)

```typescript
// ❌ Each node fetches its own code - no sharing
const EnhancedNode = ({ data }) => {
  const { data: codeData } = useEditorCode(data.nodeId);
  const { editorValue, handleSave } = useEditableCode(data.nodeId);
  // ... 300 lines of mixed concerns
};
```

### After (Clean Pattern)

```typescript
// ✅ Split into Container and Presentational

// Container - handles data fetching
const CanvasNodeContainer = memo(({ data }) => {
  const { data: codeData, isLoading: codeLoading } = useCode(data.nodeId);
  const { data: logsData } = useLogsForNode(data.nodeId);
  const { mutate: writeCode, isPending } = useWriteCode();
  
  const handleSaveCode = (code: string) => {
    writeCode({ nodeId: data.nodeId, code });
  };
  
  return (
    <CanvasNodeUI
      data={data}
      code={codeData?.code}
      codeLoading={codeLoading}
      logs={logsData}
      onSaveCode={handleSaveCode}
      isSaving={isPending}
    />
  );
});

// Presentational - pure UI
const CanvasNodeUI = memo(({
  data,
  code,
  codeLoading,
  logs,
  onSaveCode,
  isSaving,
}) => {
  const [showCode, setShowCode] = useState(false);
  const [localCode, setLocalCode] = useState(code ?? '');
  
  // Sync local with server code
  useEffect(() => {
    if (code) setLocalCode(code);
  }, [code]);
  
  const hasChanges = localCode !== code;
  
  return (
    <div className="canvas-node">
      <NodeHeader data={data} />
      
      {showCode ? (
        <NodeCodeSection
          code={localCode}
          onChange={setLocalCode}
          onSave={() => onSaveCode(localCode)}
          hasChanges={hasChanges}
          isSaving={isSaving}
          isLoading={codeLoading}
        />
      ) : (
        <NodeDescription description={data.metadata?.description} />
      )}
      
      {logs && logs.length > 0 && (
        <NodeLogsIndicator logCount={logs.length} />
      )}
      
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
});
```

---

## 📡 Real-Time Updates via Socket

```typescript
// hooks/useCanvasSync.ts
import { useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { useSocketContext } from '@/services/socket';
import { queryKeys } from '@/services/queryKeys';

export function useCanvasSync() {
  const { socket, isConnected } = useSocketContext();
  const queryClient = useQueryClient();
  
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    // Code updated in another tab/user
    const onCodeUpdated = ({ nodeId }: { nodeId: string }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(nodeId),
      });
    };
    
    // New logs arrived
    const onLogsNew = ({ nodeId }: { nodeId: string }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.logs.tree(nodeId),
      });
    };
    
    // Node structure changed (affects canvas layout)
    const onNodeUpdated = ({ projectId }: { projectId: string }) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.tree(projectId),
      });
    };
    
    socket.on('code:updated', onCodeUpdated);
    socket.on('logs:new', onLogsNew);
    socket.on('node:updated', onNodeUpdated);
    
    return () => {
      socket.off('code:updated', onCodeUpdated);
      socket.off('logs:new', onLogsNew);
      socket.off('node:updated', onNodeUpdated);
    };
  }, [socket, isConnected, queryClient]);
}
```

### Use in Canvas

```typescript
// CanvasView.tsx
function CanvasView({ projectId }: { projectId: string }) {
  // Subscribe to real-time updates
  useCanvasSync();
  useProjectRoom(projectId); // Join socket room
  
  // ... rest of canvas
}
```

---

## 🔗 Syncing with Other UI Components

### Code Editor (Main Panel)

```typescript
// Code/index.tsx - Uses SAME hooks, SAME cache
function CodeEditor() {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const { data: codeData } = useCode(selectedNode?._key);
  const { mutate: writeCode } = useWriteCode();
  
  // When this saves, Canvas nodes auto-update!
  const handleSave = (code: string) => {
    if (selectedNode) {
      writeCode({ nodeId: selectedNode._key, code });
    }
  };
  
  // ...
}
```

### Logs Sidebar

```typescript
// LogsSidebar.tsx - Uses SAME useLogsForNode hook
function LogsSidebar() {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const { data: logs } = useLogsForNode(selectedNode?._key);
  
  // Same cache as Canvas nodes!
  return <LogsList logs={logs ?? []} />;
}
```

### Right Panel

```typescript
// RightSidebar/LogsSection.tsx
function LogsSection({ nodeId }: { nodeId: string }) {
  const { data: logs, isLoading } = useLogsForNode(nodeId);
  
  if (isLoading) return <LogsSkeleton />;
  return <LogsTree logs={logs ?? []} />;
}
```

---

## 🎯 Summary: The Sync Pattern

1. **Define shared query hooks** (`useCode`, `useLogsForNode`)
2. **Use same hooks everywhere** (Canvas, Editor, Sidebar)
3. **Mutations invalidate queries** (one save updates all)
4. **Socket events trigger invalidation** (real-time sync)

```
┌─────────────────────────────────────────────────────────────┐
│                    TanStack Query Cache                     │
│              (Single Source of Truth)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
  ┌───────────┐       ┌───────────┐       ┌───────────┐
  │   Canvas  │       │   Editor  │       │  Sidebar  │
  │   Nodes   │       │           │       │           │
  └─────┬─────┘       └─────┬─────┘       └───────────┘
        │                   │
        │  useWriteCode()   │
        │         │         │
        └─────────┼─────────┘
                  ▼
           invalidateQueries()
                  │
                  ▼
         All components refetch
```

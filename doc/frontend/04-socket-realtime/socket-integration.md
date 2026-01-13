# Socket.io Integration

## 🎯 Goal

Integrate real-time updates with your React app cleanly.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React App                            │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              SocketProvider                      │   │
│  │  (Provides socket instance via Context)          │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │            useSocketEvents Hook                  │   │
│  │  (Connects socket events to React Query)         │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────▼───────────────────────────┐   │
│  │              TanStack Query                      │   │
│  │  (Cache is invalidated, components re-render)    │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Socket Service Structure

```
services/
└── socket/
    ├── index.ts           # Public exports
    ├── socket.ts          # Socket instance & connection
    ├── SocketProvider.tsx # React context provider
    ├── useSocket.ts       # Access socket hook
    └── useSocketEvents.ts # Event subscription hook
```

---

## 🔌 Socket Instance

```typescript
// services/socket/socket.ts
import io, { Socket } from 'socket.io-client';

let socket: Socket | null = null;

const getSocketUrl = (): string => {
  const envUrl = import.meta.env.VITE_SOCKET_URL;
  if (envUrl) return envUrl;
  
  // Development default
  if (import.meta.env.DEV) {
    return 'http://localhost:8000';
  }
  
  // Production: same origin
  return window.location.origin;
};

export const createSocket = (): Socket => {
  if (socket?.connected) {
    return socket;
  }
  
  socket = io(getSocketUrl(), {
    path: '/ws/socket.io/',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
  });
  
  // Debug logging
  if (import.meta.env.DEV) {
    socket.onAny((event, ...args) => {
      console.log(`[Socket] ${event}`, args);
    });
  }
  
  return socket;
};

export const getSocket = (): Socket | null => socket;

export const disconnectSocket = (): void => {
  socket?.disconnect();
  socket = null;
};
```

---

## 🎁 Socket Context Provider

```typescript
// services/socket/SocketProvider.tsx
import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { Socket } from 'socket.io-client';
import { createSocket, disconnectSocket } from './socket';

interface SocketContextValue {
  socket: Socket | null;
  isConnected: boolean;
}

const SocketContext = createContext<SocketContextValue>({
  socket: null,
  isConnected: false,
});

export const useSocketContext = () => useContext(SocketContext);

export function SocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  
  useEffect(() => {
    // Create socket on mount
    const socket = createSocket();
    socketRef.current = socket;
    
    const onConnect = () => setIsConnected(true);
    const onDisconnect = () => setIsConnected(false);
    
    socket.on('connect', onConnect);
    socket.on('disconnect', onDisconnect);
    
    // Set initial state
    setIsConnected(socket.connected);
    
    return () => {
      socket.off('connect', onConnect);
      socket.off('disconnect', onDisconnect);
      disconnectSocket();
    };
  }, []);
  
  return (
    <SocketContext.Provider value={{ socket: socketRef.current, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
}
```

---

## 🎣 useSocket Hook

```typescript
// services/socket/useSocket.ts
import { useEffect } from 'react';
import { useSocketContext } from './SocketProvider';

// Simple access hook
export const useSocket = () => {
  const { socket, isConnected } = useSocketContext();
  return { socket, isConnected };
};

// Join a project room
export const useProjectRoom = (projectId: string | undefined) => {
  const { socket, isConnected } = useSocketContext();
  
  useEffect(() => {
    if (!socket || !isConnected || !projectId) return;
    
    socket.emit('join_project', projectId);
    
    return () => {
      socket.emit('leave_project', projectId);
    };
  }, [socket, isConnected, projectId]);
};
```

---

## 📡 useSocketEvents - TanStack Query Integration

```typescript
// services/socket/useSocketEvents.ts
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../queryKeys';
import { useSocketContext } from './SocketProvider';

interface SocketEvents {
  // Define your socket event types
  'project:updated': { projectId: string };
  'code:updated': { elementId: string };
  'logs:new': { nodeId: string };
  'node:created': { projectId: string; nodeId: string };
  'node:deleted': { projectId: string; nodeId: string };
}

export function useSocketEvents() {
  const { socket, isConnected } = useSocketContext();
  const queryClient = useQueryClient();
  
  useEffect(() => {
    if (!socket || !isConnected) return;
    
    // Project updates
    const onProjectUpdated = ({ projectId }: SocketEvents['project:updated']) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.tree(projectId),
      });
    };
    
    // Code updates
    const onCodeUpdated = ({ elementId }: SocketEvents['code:updated']) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(elementId),
      });
    };
    
    // New logs
    const onNewLogs = ({ nodeId }: SocketEvents['logs:new']) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.logs.tree(nodeId),
      });
    };
    
    // Subscribe
    socket.on('project:updated', onProjectUpdated);
    socket.on('code:updated', onCodeUpdated);
    socket.on('logs:new', onNewLogs);
    
    // Cleanup
    return () => {
      socket.off('project:updated', onProjectUpdated);
      socket.off('code:updated', onCodeUpdated);
      socket.off('logs:new', onNewLogs);
    };
  }, [socket, isConnected, queryClient]);
}
```

---

## 🔧 Setup in App

```typescript
// main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SocketProvider } from '@/services/socket';
import { App } from './App';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <SocketProvider>
      <App />
    </SocketProvider>
  </QueryClientProvider>
);
```

```typescript
// App.tsx or Dashboard layout
import { useSocketEvents } from '@/services/socket';

function AppLayout({ children }: { children: React.ReactNode }) {
  // Subscribe to socket events at app level
  useSocketEvents();
  
  return <>{children}</>;
}
```

---

## 📖 Next Steps

- **[../06-component-patterns/overview.md](../06-component-patterns/overview.md)** - Component design patterns

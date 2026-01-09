# Step 4: Create Socket Provider

## Goal
Wrap socket.io in a React Context so components can easily access it.

## Why
Your current `services/socket.ts` exports raw functions. This makes it hard to:
- Know when socket is connected
- Clean up listeners properly
- Use socket state in components

---

## What to Change

### Restructure `src/frontend/src/services/socket/`

```
src/frontend/src/services/socket/
├── index.ts           # Public exports
├── socket.ts          # Connection logic (keep most of existing)
├── SocketProvider.tsx # NEW: React Context
└── hooks.ts           # NEW: useSocket, useProjectRoom
```

---

### File 1: Keep `socket.ts` but simplify

```typescript
// src/frontend/src/services/socket/socket.ts
import io, { Socket } from 'socket.io-client';

let socket: Socket | null = null;

const getConfig = () => {
  const apiBase = import.meta.env.VITE_API_BASE_URL || '';
  
  if (apiBase.includes('localhost') || !apiBase) {
    return { url: 'http://localhost:8000', path: '/ws/socket.io/' };
  }
  
  return { url: window.location.origin, path: '/ws/socket.io/' };
};

export const createSocket = (): Socket => {
  if (socket?.connected) return socket;
  
  const config = getConfig();
  
  socket = io(config.url, {
    path: config.path,
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
  });
  
  return socket;
};

export const getSocket = (): Socket | null => socket;

export const disconnectSocket = (): void => {
  socket?.disconnect();
  socket = null;
};
```

---

### File 2: NEW `SocketProvider.tsx`

```typescript
// src/frontend/src/services/socket/SocketProvider.tsx
import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
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

interface SocketProviderProps {
  children: ReactNode;
}

export function SocketProvider({ children }: SocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    const socket = createSocket();
    socketRef.current = socket;

    const onConnect = () => {
      console.log('🔌 Socket connected:', socket.id);
      setIsConnected(true);
    };

    const onDisconnect = (reason: string) => {
      console.log('🔌 Socket disconnected:', reason);
      setIsConnected(false);
    };

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

### File 3: NEW `hooks.ts`

```typescript
// src/frontend/src/services/socket/hooks.ts
import { useEffect } from 'react';
import { useSocketContext } from './SocketProvider';

export const useSocket = () => {
  const { socket, isConnected } = useSocketContext();
  return { socket, isConnected };
};

/**
 * Join a project-specific room to receive updates
 */
export const useProjectRoom = (projectId: string | undefined) => {
  const { socket, isConnected } = useSocketContext();

  useEffect(() => {
    if (!socket || !isConnected || !projectId) return;

    socket.emit('join_project', projectId);
    console.log(`📦 Joined project room: ${projectId}`);

    return () => {
      socket.emit('leave_project', projectId);
      console.log(`📦 Left project room: ${projectId}`);
    };
  }, [socket, isConnected, projectId]);
};
```

---

### File 4: Update `index.ts`

```typescript
// src/frontend/src/services/socket/index.ts
export { SocketProvider, useSocketContext } from './SocketProvider';
export { useSocket, useProjectRoom } from './hooks';
export { getSocket, disconnectSocket } from './socket';
```

---

## Add Provider to App

### In `main.tsx`

```diff
+ import { SocketProvider } from '@/services/socket';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
+   <SocketProvider>
      <RouterProvider router={router} />
+   </SocketProvider>
  </QueryClientProvider>
);
```

---

## Verification

- [ ] Socket connects on app load (check console)
- [ ] No errors when navigating

---

## Next Step

👉 [Step 5: Connect Socket to React Query](./step-05-socket-sync.md)

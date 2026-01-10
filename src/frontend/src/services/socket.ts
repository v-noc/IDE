import { useEffect } from 'react';

// ... existing code ...

export const useSocketConnection = () => {
  useEffect(() => {
    initSocket();
    return () => {
      disconnectSocket();
    };
  }, []);
};

const getSocketConfig = (): { url: string; path: string } => {
  const envUrl = import.meta.env.VITE_SOCKET_URL;
  if (envUrl) {
    // If full URL is provided, extract base URL and path
    try {
      const urlObj = new URL(envUrl);
      return {
        url: `${urlObj.protocol}//${urlObj.host}`,
        path: urlObj.pathname || '/socket.io/',
      };
    } catch {
      return { url: envUrl, path: '/socket.io/' };
    }
  }

  // Default to same origin with /ws path (backend mounts socket at /ws)
  const apiBase = import.meta.env.VITE_API_BASE_URL || '';

  // In development, connect to localhost:8000
  // Note: browsers cannot connect to 0.0.0.0, must use localhost or 127.0.0.1
  if (apiBase.includes('localhost') || apiBase.includes('127.0.0.1') || apiBase.includes('0.0.0.0') || !apiBase) {
    // Development: connect to base URL and specify /ws/socket.io/ path
    return {
      url: 'http://localhost:8000',
      path: '/ws/socket.io/',
    };
  }

  // Production: use same origin with /ws/socket.io/ path
  return {
    url: window.location.origin,
    path: '/ws/socket.io/',
  };
};

const logWithTimestamp = (message: string, type: 'info' | 'error' | 'warn' = 'info') => {
  const timestamp = new Date().toLocaleTimeString();
  const prefix = type === 'error' ? '❌' : type === 'warn' ? '⚠️' : '🔌';
  console.log(`${prefix} [${timestamp}] Socket: ${message}`);
};

export const initSocket = (): Socket<DefaultEventsMap, DefaultEventsMap> => {
  if (socket?.connected) {
    logWithTimestamp('Socket already connected, reusing existing connection');
    return socket;
  }

  const config = getSocketConfig();
  logWithTimestamp(`Initializing connection to ${config.url}${config.path}`);

  socket = io(config.url, {
    path: config.path,
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
    reconnectionDelayMax: 5000,
  });

  // Connection event handlers
  socket.on('connect', () => {
    logWithTimestamp(`Connected successfully - Socket ID: ${socket?.id?.substring(0, 8)}...`);
  });

  socket.on('disconnect', (reason) => {
    logWithTimestamp(`Disconnected - Reason: ${reason}`, 'warn');
  });

  socket.on('connect_error', (error) => {
    logWithTimestamp(`Connection error: ${error.message}`, 'error');
  });

  socket.on('reconnect', (attemptNumber) => {
    logWithTimestamp(`Reconnected after ${attemptNumber} attempt(s)`);
  });

  socket.on('reconnect_attempt', (attemptNumber) => {
    logWithTimestamp(`Reconnection attempt ${attemptNumber}...`, 'warn');
  });

  socket.on('reconnect_error', (error) => {
    logWithTimestamp(`Reconnection error: ${error.message}`, 'error');
  });

  socket.on('reconnect_failed', () => {
    logWithTimestamp('Reconnection failed after all attempts', 'error');
  });

  return socket;
};

export const getSocket = (): Socket<DefaultEventsMap, DefaultEventsMap> | null => {
  if (!socket) {
    logWithTimestamp('Socket not initialized, initializing now...', 'warn');
    initSocket();
  }
  return socket;
};

export const disconnectSocket = () => {
  if (socket) {
    logWithTimestamp('Disconnecting socket...');
    socket.disconnect();
    socket = null;
    logWithTimestamp('Socket disconnected and cleared');
  }
};

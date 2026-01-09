import io, { Socket } from 'socket.io-client';

let socket: Socket | null = null;

const getConfig = () => {
  const apiBase = import.meta.env.VITE_SOCKET_URL

  return { url: apiBase, path: '/ws/socket.io/' };
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
}

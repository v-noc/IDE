import io, { Socket } from 'socket.io-client';
import type { ServerToClientEvents, ClientToServerEvents } from './types';

let socket: Socket<ServerToClientEvents, ClientToServerEvents> | null = null;

const getConfig = () => {
  const apiBase = import.meta.env.VITE_SOCKET_URL

  return { url: apiBase, path: '/ws/socket.io/' };
};

export const createSocket = (): Socket<ServerToClientEvents, ClientToServerEvents> => {
  if (socket?.connected) return socket;
  const config = getConfig();

  socket = io<ServerToClientEvents, ClientToServerEvents>(config.url, {
    path: config.path,
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
  });

  return socket;
};

export const getSocket = (): Socket<ServerToClientEvents, ClientToServerEvents> | null => socket;

export const disconnectSocket = (): void => {
  socket?.disconnect();
  socket = null;
}

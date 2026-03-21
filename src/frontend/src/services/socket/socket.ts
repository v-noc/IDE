import io, { Socket } from "socket.io-client";
import type { ServerToClientEvents, ClientToServerEvents } from "./types";

let socket: Socket<ServerToClientEvents, ClientToServerEvents> | null = null;

/**
 * Browsers cannot connect to 0.0.0.0 — normalize to localhost.
 * Also align socket origin with API origin when VITE_SOCKET_URL is unset.
 */
function normalizeBrowserOrigin(raw: string): string {
  const trimmed = raw.replace(/\/$/, "");
  try {
    const u = new URL(trimmed);
    if (u.hostname === "0.0.0.0") {
      u.hostname = "localhost";
    }
    return u.origin;
  } catch {
    return trimmed;
  }
}

function socketOrigin(): string {
  const explicit = import.meta.env.VITE_SOCKET_URL as string | undefined;
  if (explicit?.trim()) {
    return normalizeBrowserOrigin(explicit.trim());
  }
  const api = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (api?.startsWith("http")) {
    try {
      return normalizeBrowserOrigin(new URL(api).origin);
    } catch {
      /* fall through */
    }
  }
  if (typeof window !== "undefined") {
    return window.location.origin;
  }
  return "";
}

/** Path must match FastAPI `mount("/ws", ...)` + Socket.IO (see backend `SocketIOMount`). */
function socketPath(): string {
  const fromEnv = (import.meta.env.VITE_SOCKET_IO_PATH as string | undefined)?.replace(
    /\/?$/,
    "",
  );
  return fromEnv || "/ws/socket.io";
}

const getConfig = () => ({
  url: socketOrigin(),
  path: socketPath(),
});

export const createSocket = (): Socket<ServerToClientEvents, ClientToServerEvents> => {
  if (socket?.connected) return socket;
  const config = getConfig();

  socket = io<ServerToClientEvents, ClientToServerEvents>(config.url, {
    path: config.path,
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 5,
    autoConnect: true,
  });

  return socket;
};

export const getSocket = (): Socket<ServerToClientEvents, ClientToServerEvents> | null =>
  socket;

export const disconnectSocket = (): void => {
  socket?.disconnect();
  socket = null;
};

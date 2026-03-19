import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { Socket } from "socket.io-client";
import { createSocket, disconnectSocket } from "./socket";
import type { ServerToClientEvents, ClientToServerEvents } from "./types";

interface SocketContextValue {
  socket: Socket<ServerToClientEvents, ClientToServerEvents> | null;
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
  const [socket, setSocket] = useState<Socket<
    ServerToClientEvents,
    ClientToServerEvents
  > | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const s = createSocket();
    setSocket(s);

    const onConnect = () => {
      setIsConnected(true);
    };

    const onDisconnect = () => {
      setIsConnected(false);
    };

    s.on("connect", onConnect);
    s.on("disconnect", onDisconnect);
    setIsConnected(s.connected);

    return () => {
      s.off("connect", onConnect);
      s.off("disconnect", onDisconnect);
      disconnectSocket();
      setSocket(null);
      setIsConnected(false);
    };
  }, []);

  return (
    <SocketContext.Provider value={{ socket, isConnected }}>
      {children}
    </SocketContext.Provider>
  );
}

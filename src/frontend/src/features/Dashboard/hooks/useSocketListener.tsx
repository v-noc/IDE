import { getSocket } from "@/services/socket";
import { useEffect } from "react";

interface SocketListenerProps {
  event: string;
  callback: (...args: unknown[]) => void;
}
export const useSocketListener = ({ event, callback }: SocketListenerProps) => {
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    socket.on(event, callback);

    return () => {
      socket.off(event, callback);
    };
  }, [event, callback]);
};

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

/**
 * Hook to join a project room for receiving project-specific socket events.
 * The backend emits events to rooms named by project ID (_id field).
 */
export const useJoinProjectRoom = (projectId: string | null | undefined) => {
  useEffect(() => {
    if (!projectId) return;

    const socket = getSocket();
    if (!socket) return;

    const joinRoom = () => {
      if (socket && socket.connected) {
        socket.emit("join_project", projectId);
      }
    };

    // Join immediately if already connected
    if (socket.connected) {
      joinRoom();
    } else {
      // Wait for connection if not connected yet
      socket.once("connect", joinRoom);
    }

    // Cleanup: remove the connect listener if component unmounts before connection
    return () => {
      if (socket) {
        socket.off("connect", joinRoom);
      }
    };
  }, [projectId]);
};

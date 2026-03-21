import { useEffect } from "react";
import { useSocketContext } from "./SocketProvider";

export const useSocket = () => {
  const { socket, isConnected } = useSocketContext();
  return { socket, isConnected };
};

/**
 * Join a project-specific room to receive updates.
 * Re-joins on every socket `connect` (reconnect); do not rely only on React `isConnected`
 * to avoid missing the first join when state lags the handshake.
 */
export const useProjectRoom = (projectId: string | undefined) => {
  const { socket } = useSocketContext();
  useEffect(() => {
    if (!socket || !projectId) return;

    const join = () => {
      if (socket.connected) {
        socket.emit("join_project", projectId);
      }
    };

    join();
    socket.on("connect", join);

    return () => {
      socket.off("connect", join);
      if (socket.connected) {
        socket.emit("leave_project", projectId);
      }
    };
  }, [socket, projectId]);
};

/**
 * Join `conv:{conversationId}` for agent JSON patches and stream events.
 */
export const useConversationRoom = (
  conversationId: string | undefined | null,
) => {
  const { socket } = useSocketContext();
  useEffect(() => {
    if (!socket || !conversationId) return;

    const join = () => {
      if (socket.connected) {
        socket.emit("join_conversation", conversationId);
      }
    };

    join();
    socket.on("connect", join);

    return () => {
      socket.off("connect", join);
      if (socket.connected) {
        socket.emit("leave_conversation", conversationId);
      }
    };
  }, [socket, conversationId]);
};

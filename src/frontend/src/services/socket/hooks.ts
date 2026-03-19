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
    console.log("Socket connected:", socket);
    console.log("Is connected:", isConnected);
    console.log("Project ID:", projectId);
    if (!socket || !isConnected || !projectId) return;

    socket.emit("join_project", projectId);
    console.log(`📦 Joined project room: ${projectId}`);

    return () => {
      socket.emit("leave_project", projectId);
      console.log(`📦 Left project room: ${projectId}`);
    };
  }, [socket, isConnected, projectId]);
};

/**
 * Join `conv:{conversationId}` for agent JSON patches and stream events.
 */
export const useConversationRoom = (
  conversationId: string | undefined | null,
) => {
  const { socket, isConnected } = useSocketContext();
  useEffect(() => {
    if (!socket || !isConnected || !conversationId) return;

    socket.emit("join_conversation", conversationId);

    return () => {
      socket.emit("leave_conversation", conversationId);
    };
  }, [socket, isConnected, conversationId]);
};

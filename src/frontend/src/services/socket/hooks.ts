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

    socket.emit("join_project", projectId);
    console.log(`📦 Joined project room: ${projectId}`);

    return () => {
      socket.emit("leave_project", projectId);
      console.log(`📦 Left project room: ${projectId}`);
    };
  }, [socket, isConnected, projectId]);
}

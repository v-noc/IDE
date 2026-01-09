import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { useSocketContext } from "./SocketProvider";

/**
 * Syncs socket events to React Query cache.
 * Call this once at app level (e.g., in Dashboard layout).
 */
export function useSocketSync() {
  const { socket, isConnected } = useSocketContext();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!socket || !isConnected) return;

    // When code is updated (from backend processing or another user)
    const onCodeUpdated = (data: { element_id: string }) => {
      console.log('🔄 Code updated:', data.element_id);
      queryClient.invalidateQueries({
        queryKey: queryKeys.code.detail(data.element_id),
      });
    };

    // When new logs are created
    const onLogsNew = (data: { node_id: string }) => {
      console.log('🔄 New logs:', data.node_id);
      queryClient.invalidateQueries({
        queryKey: queryKeys.logs.tree(data.node_id),
      });
    };

    // When project structure changes
    const onProjectUpdated = (data: { project_id: string }) => {
      console.log('🔄 Project updated:', data.project_id);
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.tree(data.project_id),
      });
    };

    // Subscribe to events
    socket.on("code:updated", onCodeUpdated);
    socket.on("logs:new", onLogsNew);
    socket.on("project:updated", onProjectUpdated);

    return () => {
      socket.off("code:updated", onCodeUpdated);
      socket.off("logs:new", onLogsNew);
      socket.off("project:updated", onProjectUpdated);
    };
  }, [socket, isConnected, queryClient])
}

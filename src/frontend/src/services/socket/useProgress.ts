import { useEffect, useState, useCallback } from "react";
import { useSocketContext } from "./SocketProvider";
import type { ProgressEventPayload } from "@/types/progress";

/**
 * Hook to listen for project progress events
 * 
 * @param projectId - The project ID to listen for progress updates
 * @returns Current progress state and handler function
 */
export function useProgress(projectId: string | undefined) {
  const { socket, isConnected } = useSocketContext();
  const [progress, setProgress] = useState<ProgressEventPayload | null>(null);

  useEffect(() => {
    if (!socket || !isConnected || !projectId) {
      setProgress(null);
      return;
    }

    const onProgress = (payload: ProgressEventPayload) => {
      // Only update if this progress event is for the current project
      if (payload.project_id === projectId) {
        setProgress(payload);
      }
    };

    socket.on("project:progress", onProgress);

    return () => {
      socket.off("project:progress", onProgress);
    };
  }, [socket, isConnected, projectId]);

  const clearProgress = useCallback(() => {
    setProgress(null);
  }, []);

  return {
    progress,
    clearProgress,
    isProcessing: progress?.status === "running",
  };
}

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { type ProgressEventPayload } from "@/types/progress";
import { useSocketContext } from "./SocketProvider";

interface ProgressContextValue {
  progress: ProgressEventPayload | null;
  setProgress: (progress: ProgressEventPayload | null) => void;
  clearProgress: (projectId?: string) => void;
  isProcessing: boolean;
  getProgressForProject: (projectId: string) => ProgressEventPayload | null;
}

const ProgressContext = createContext<ProgressContextValue>({
  progress: null,
  setProgress: () => {},
  clearProgress: () => {},
  isProcessing: false,
  getProgressForProject: () => null,
});

export const useProgressContext = () => useContext(ProgressContext);

interface ProgressProviderProps {
  children: ReactNode;
}

/**
 * Provider that manages progress state for all projects
 * Listens to socket events and maintains progress state
 */
export function ProgressProvider({ children }: ProgressProviderProps) {
  const { socket, isConnected } = useSocketContext();
  const [progressMap, setProgressMap] = useState<
    Map<string, ProgressEventPayload>
  >(new Map());

  // Listen for progress events
  useEffect(() => {
    if (!socket || !isConnected) return;

    const onProgress = (payload: ProgressEventPayload) => {
      setProgressMap((prev) => {
        const next = new Map(prev);
        next.set(payload.project_id, payload);
        return next;
      });
    };

    socket.on("project:progress", onProgress);

    return () => {
      socket.off("project:progress", onProgress);
    };
  }, [socket, isConnected]);

  const setProgress = useCallback((progress: ProgressEventPayload | null) => {
    if (!progress) return;
    setProgressMap((prev) => {
      const next = new Map(prev);
      next.set(progress.project_id, progress);
      return next;
    });
  }, []);

  const clearProgress = useCallback((projectId?: string) => {
    if (projectId) {
      setProgressMap((prev) => {
        const next = new Map(prev);
        next.delete(projectId);
        return next;
      });
    } else {
      setProgressMap(new Map());
    }
  }, []);

  const getProgressForProject = useCallback(
    (projectId: string) => {
      return progressMap.get(projectId) || null;
    },
    [progressMap],
  );

  // Get the most recent progress (or first one if multiple)
  const currentProgress =
    progressMap.size > 0
      ? Array.from(progressMap.values())[progressMap.size - 1]
      : null;

  const value: ProgressContextValue = {
    progress: currentProgress,
    setProgress,
    clearProgress,
    isProcessing: currentProgress?.status === "running",
    getProgressForProject,
  };

  return (
    <ProgressContext.Provider value={value}>
      {children}
    </ProgressContext.Provider>
  );
}

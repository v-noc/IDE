import { ProgressEventPayload } from "@/types/progress";

/**
 * Socket event types for client-server communication
 */
export interface ServerToClientEvents {
  // Progress tracking
  "project:progress": (payload: ProgressEventPayload) => void;
  
  // Code updates
  "code:updated": (data: { element_id: string }) => void;
  
  // Logs updates
  "logs:new": (data: { node_id: string }) => void;
  
  // Project updates
  "project:updated": (data: { project_id: string }) => void;
  
  // Connection events
  connect: () => void;
  disconnect: (reason: string) => void;
}

/**
 * Client-to-server event types
 */
export interface ClientToServerEvents {
  // Project room management
  join_project: (projectId: string) => void;
  leave_project: (projectId: string) => void;
}

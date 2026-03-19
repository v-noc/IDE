import { ProgressEventPayload } from "@/types/progress";
import type {
  ConversationPatchPayload,
  StreamChunkPayload,
  StreamEndPayload,
  StreamErrorPayload,
  StreamStartPayload,
} from "@/types/agent/stream";

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

  // Agent / conversations (see doc/agentv2/07-chat-streaming.md, 08-json-patch-protocol.md)
  "conversation:patch": (payload: ConversationPatchPayload) => void;
  "stream:start": (payload: StreamStartPayload) => void;
  "stream:chunk": (payload: StreamChunkPayload) => void;
  "stream:end": (payload: StreamEndPayload) => void;
  "stream:error": (payload: StreamErrorPayload) => void;

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

  /** Subscribe to `conversation:*` and `stream:*` for one conversation */
  join_conversation: (conversationId: string) => void;
  leave_conversation: (conversationId: string) => void;

  /** Replay chunks after reconnect (server event name `stream:resume`) */
  "stream:resume": (data: { stream_id: string; last_seq: number }) => void;
}

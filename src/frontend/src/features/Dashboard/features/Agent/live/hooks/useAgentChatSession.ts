import { useAgentConversationSocket } from "./useAgentConversationSocket";
import { useAgentConversationSync } from "./useAgentConversationSync";

/**
 * Full live session: REST hydration + WebSocket room, patches, and streams.
 */
export function useAgentChatSession(
  backendConversationId: string | null,
  projectId: string,
) {
  useAgentConversationSync(backendConversationId, projectId);
  useAgentConversationSocket(backendConversationId, projectId);
}

/**
 * Workflow runs attach tasks to a conversation; live updates use the same
 * socket contract as chat (`conversation:patch`, `stream:*`).
 * `useAgentChatSession` already calls `useConversationRoom` for the active conversation.
 */
export { useConversationRoom } from "@/services/socket";
export {
  AGENT_SOCKET_CLIENT_EVENTS,
  AGENT_SOCKET_SERVER_EVENTS,
} from "@/lib/agentSocket";

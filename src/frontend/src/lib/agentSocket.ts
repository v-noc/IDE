/**
 * Socket.io event names for agent conversations (chat + background workflows).
 * Subscribe with `useConversationRoom(conversationId)` from `@/services/socket`.
 * Payload types live in `@/types/agent/stream`.
 */
export const AGENT_SOCKET_SERVER_EVENTS = {
  conversationPatch: "conversation:patch",
  streamStart: "stream:start",
  streamChunk: "stream:chunk",
  streamEnd: "stream:end",
  streamError: "stream:error",
} as const;

export const AGENT_SOCKET_CLIENT_EVENTS = {
  joinConversation: "join_conversation",
  leaveConversation: "leave_conversation",
} as const;

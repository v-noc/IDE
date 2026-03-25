import { agentFetch } from "@/lib/agentFetch";
import type {
  ConversationMetaWire,
  CreateConversationPayload,
  PaginatedResponse,
  SendMessagePayload,
  SendMessageResponse,
  WireConversation,
  WireMessage,
  WireSubTask,
} from "@/types/agent";

const Q = (params: Record<string, string | number | undefined>) => {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined) continue;
    sp.set(k, String(v));
  }
  const q = sp.toString();
  return q ? `?${q}` : "";
};

export const agentApi = {
  createConversation: (projectId: string, body: CreateConversationPayload) =>
    agentFetch<ConversationMetaWire>(
      "/conversations",
      {
        method: "POST",
        body,
      },
      projectId,
    ),

  listConversations: (projectId: string, limit = 50, cursor?: string) =>
    agentFetch<PaginatedResponse<ConversationMetaWire>>(
      `/conversations${Q({ limit, cursor })}`,
      {},
      projectId,
    ),

  getConversationMeta: (projectId: string, conversationId: string) =>
    agentFetch<ConversationMetaWire>(
      `/conversations/meta${Q({ conversation_id: conversationId })}`,
      {},
      projectId,
    ),

  listMessages: (
    projectId: string,
    conversationId: string,
    cursor = 0,
    limit = 50,
  ) =>
    agentFetch<PaginatedResponse<WireMessage>>(
      `/conversations/messages${Q({
        conversation_id: conversationId,
        cursor,
        limit,
      })}`,
      {},
      projectId,
    ),

  /** Builds a full wire conversation for the client store (meta + first page of messages). */
  hydrateConversation: async (
    projectId: string,
    conversationId: string,
    messageLimit = 200,
  ): Promise<WireConversation> => {
    const meta = await agentApi.getConversationMeta(projectId, conversationId);
    const page = await agentApi.listMessages(
      projectId,
      conversationId,
      0,
      messageLimit,
    );
    return {
      id: meta.id,
      title: meta.title,
      description: meta.description,
      message_count: meta.message_count,
      has_active_task: meta.has_active_task,
      created_at: meta.created_at,
      updated_at: meta.updated_at,
      metadata: meta.metadata ?? {},
      messages: page.items,
    };
  },

  sendMessage: (projectId: string, payload: SendMessagePayload) =>
    agentFetch<SendMessageResponse>(
      "/conversations/messages",
      {
        method: "POST",
        body: payload,
      },
      projectId,
    ),

  listTaskSubtasks: (
    projectId: string,
    taskId: string,
    cursor = 0,
    limit = 200,
  ) =>
    agentFetch<PaginatedResponse<WireSubTask>>(
      `/tasks/subtasks${Q({
        task_id: taskId,
        cursor,
        limit,
      })}`,
      {},
      projectId,
    ),
};

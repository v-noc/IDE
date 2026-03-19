import type { ChatCompletionParams } from "./generation";

export interface PaginatedResponse<T> {
  items: T[];
  next_cursor?: string | number | null;
  has_more: boolean;
}

export interface SendMessagePayload {
  conversation_id: string;
  role?: "user";
  parts: Array<{ type: "text"; text: string }>;
  generation?: ChatCompletionParams | null;
  client_ref?: string | null;
  metadata?: Record<string, unknown> | null;
}

export interface SendMessageResponse {
  message_id: string | null;
  task_id: string;
  conversation_id: string;
  stream_id: string;
  client_ref?: string | null;
}

export interface CreateConversationPayload {
  title?: string;
  description?: string;
}

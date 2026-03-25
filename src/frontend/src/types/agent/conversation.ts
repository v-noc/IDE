/** Wire shapes aligned with backend `conversation_message_to_wire` + metadata. */

export type WireMessageRole = "user" | "assistant" | "system" | string;

export interface WireTextPart {
  type: "text";
  text: string;
}

/** Sub-task row from `GET /tasks/subtasks` or embedded in a task message part. */
export interface WireSubTask {
  id?: string;
  name?: string;
  title?: string;
  description?: string;
  state?: string;
  sequence?: number;
}

export type WireMessagePart = WireTextPart | Record<string, unknown>;

export interface WireMessage {
  id: string;
  role: WireMessageRole;
  sequence: number;
  parts: WireMessagePart[];
  created_at?: string;
  token_count?: number | null;
  model?: string | null;
}

export interface WireConversation {
  id: string;
  title: string;
  description: string;
  message_count: number;
  has_active_task: boolean;
  created_at: string;
  updated_at: string;
  messages: WireMessage[];
  metadata?: Record<string, unknown>;
  tasks?: Record<string, unknown>;
}

export interface ConversationMetaWire {
  id: string;
  title: string;
  description: string;
  message_count: number;
  has_active_task: boolean;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, unknown>;
}

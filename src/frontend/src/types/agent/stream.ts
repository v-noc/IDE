import type { Operation } from "fast-json-patch";

/** WebSocket payloads (server → client) for chat streaming. */

export interface StreamStartPayload {
  stream_id: string;
  conversation_id: string;
  task_id?: string | null;
  model?: string;
  provider?: string;
  client_ref?: string | null;
}

export interface StreamChunkPayload {
  stream_id: string;
  seq: number;
  delta: string;
  /** Present when merged in the client (server may omit). */
  conversation_id?: string;
}

export interface StreamEndPayload {
  stream_id: string;
  message_id: string;
  total_seq: number;
}

export interface StreamErrorPayload {
  stream_id: string;
  error: string;
}

export interface ConversationPatchPayload {
  conversation_id: string;
  patches: Operation[];
}

/** Wire types mirroring `app/agent/schemas` — hand-kept small. */

export type ConversationStatus =
  | "idle"
  | "running"
  | "awaiting_confirmation"
  | "error";

export type EffortLevel = "off" | "low" | "medium" | "high";

export type StopReason = "end_turn" | "max_steps" | "cancelled" | "error";

export interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  reasoning_tokens: number;
  cache_read_tokens: number;
}

export interface MessageMetadata {
  model_id?: string | null;
  prompt_version?: string | null;
  effort?: EffortLevel | null;
  usage?: TokenUsage | null;
  cost_usd?: number | null;
  duration_ms?: number | null;
  stop_reason?: StopReason | null;
  error?: string | null;
}

export interface TextPart {
  type: "text";
  text: string;
}

export interface NodeRefPart {
  type: "node_ref";
  node_id: string;
  name: string;
  qname?: string | null;
  node_type: string;
}

export interface DecisionPart {
  type: "decision";
  tool_call_id: string;
  decision: "approve" | "cancel";
  overrides?: Record<string, unknown>;
}

export interface ReasoningPart {
  type: "reasoning";
  origin: "native" | "summary";
  text: string;
  duration_ms?: number | null;
}

export interface ToolEstimate {
  items: number;
  llm_calls: number;
  label: string;
  over_cap: boolean;
  knobs?: Record<string, unknown>;
}

export interface ToolProgress {
  done: number;
  total: number;
  label: string;
}

export interface ArtifactRef {
  doc: string;
  render: string;
}

export type ToolState =
  | { status: "pending"; input: Record<string, unknown> }
  | {
      status: "awaiting_confirmation";
      input: Record<string, unknown>;
      estimate: ToolEstimate;
      knobs?: Record<string, unknown>;
    }
  | {
      status: "running";
      input: Record<string, unknown>;
      progress?: ToolProgress | null;
      started_at: string;
    }
  | {
      status: "completed";
      input: Record<string, unknown>;
      result: Record<string, unknown>;
      artifact?: ArtifactRef | null;
      degraded?: boolean;
      duration_ms: number;
    }
  | {
      status: "error";
      input: Record<string, unknown>;
      error: string;
      duration_ms: number;
    };

export interface ToolPart {
  type: "tool";
  tool_call_id: string;
  tool: string;
  state: ToolState;
}

export type Part =
  | TextPart
  | NodeRefPart
  | ReasoningPart
  | ToolPart
  | DecisionPart;

export interface Message {
  id: string;
  role: "user" | "assistant";
  created_at: string;
  parts: Part[];
  metadata: MessageMetadata;
}

export interface Conversation {
  id: string;
  project_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  status: ConversationStatus;
  messages: Message[];
  artifacts?: Record<string, unknown>;
  schema_version: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  updated_at: string;
  status: ConversationStatus;
}

/** JSON Patch op, plus our `append` string-concat extension. */
export type PatchOp =
  | { op: "append"; path: string; value: string }
  | { op: "add"; path: string; value: unknown }
  | { op: "remove"; path: string }
  | { op: "replace"; path: string; value: unknown }
  | { op: "move"; from: string; path: string }
  | { op: "copy"; from: string; path: string }
  | { op: "test"; path: string; value: unknown };

export type WireFrame =
  | { kind: "open"; doc: string; protocol?: number; snapshot: unknown }
  | { kind: "patch"; doc: string; seq: number; ops: PatchOp[] }
  | { kind: "close"; doc: string; status: string; message?: string | null };

export function isConversation(value: unknown): value is Conversation {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === "string" &&
    typeof v.project_id === "string" &&
    Array.isArray(v.messages)
  );
}

export function parseWireFrame(raw: unknown): WireFrame | null {
  if (!raw || typeof raw !== "object") return null;
  const frame = raw as Record<string, unknown>;
  if (frame.kind === "open") {
    if (typeof frame.doc !== "string") return null;
    return {
      kind: "open",
      doc: frame.doc,
      protocol: typeof frame.protocol === "number" ? frame.protocol : undefined,
      snapshot: frame.snapshot,
    };
  }
  if (frame.kind === "patch") {
    if (
      typeof frame.doc !== "string" ||
      typeof frame.seq !== "number" ||
      !Array.isArray(frame.ops)
    ) {
      return null;
    }
    return {
      kind: "patch",
      doc: frame.doc,
      seq: frame.seq,
      ops: frame.ops as PatchOp[],
    };
  }
  if (frame.kind === "close") {
    if (typeof frame.doc !== "string" || typeof frame.status !== "string") {
      return null;
    }
    return {
      kind: "close",
      doc: frame.doc,
      status: frame.status,
      message:
        typeof frame.message === "string" || frame.message === null
          ? (frame.message as string | null)
          : undefined,
    };
  }
  return null;
}

export type ViewMode = "chat" | "walkthrough";

export interface ConversationSummary {
  id: string;
  title: string;
  date: string;
  duration: string;
}

export type MessageRole = "user" | "assistant" | "system";

export interface ReplayEvent {
  at: number;
  type: "wait" | "click" | "focus";
  payload: Record<string, unknown>;
}

export type MessagePart =
  | {
      type: "text";
      text: string;
    }
  | {
      type: "event";
      event: ReplayEvent;
    };

export interface ConversationMessage {
  id: string;
  role: MessageRole;
  parts: MessagePart[];
}

export interface Conversation extends ConversationSummary {
  messages: ConversationMessage[];
}

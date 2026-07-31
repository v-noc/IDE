import { useEffect, useRef } from "react";
import type { Conversation, Message, Part } from "../stream/types";
import { AgentMessage } from "./AgentMessage";
import { UserMessage } from "./UserMessage";
import { findDecisionForTool, renderPart } from "./parts/registry";

type ThreadItem =
  | { kind: "user"; message: Message; key: string }
  | {
      kind: "assistant-part";
      message: Message;
      messageIndex: number;
      part: Part;
      partIndex: number;
      key: string;
    };

function isPartStreaming(
  conversation: Conversation,
  messageIndex: number,
  partIndex: number,
): boolean {
  if (conversation.status !== "running") return false;
  if (messageIndex !== conversation.messages.length - 1) return false;
  const message = conversation.messages[messageIndex];
  if (!message || message.role !== "assistant") return false;
  const part = message.parts[partIndex];
  if (!part) return false;
  if (part.type === "reasoning") return part.duration_ms == null;
  if (part.type === "text") return partIndex === message.parts.length - 1;
  return false;
}

function buildThreadItems(messages: Message[]): ThreadItem[] {
  const items: ThreadItem[] = [];

  messages.forEach((message, messageIndex) => {
    if (message.role === "user") {
      items.push({ kind: "user", message, key: message.id });
      return;
    }

    message.parts.forEach((part, partIndex) => {
      if (part.type === "decision") return;
      const key =
        part.type === "tool"
          ? part.tool_call_id
          : `${message.id}-${part.type}-${partIndex}`;
      items.push({
        kind: "assistant-part",
        message,
        messageIndex,
        part,
        partIndex,
        key,
      });
    });
  });

  return items;
}

function renderThreadItem(
  item: ThreadItem,
  conversation: Conversation,
  onFocusNode?: (part: Extract<Part, { type: "node_ref" }>) => void,
) {
  if (item.kind === "user") {
    return (
      <UserMessage message={item.message} onFocusNode={onFocusNode} />
    );
  }

  const { message, messageIndex, part, partIndex } = item;
  const rendered = renderPart(part, {
    isStreaming: isPartStreaming(conversation, messageIndex, partIndex),
    onFocusNode,
    decisionForTool: (toolCallId) =>
      findDecisionForTool(message.parts, toolCallId),
  });

  if (rendered == null) return null;

  if (part.type === "tool") {
    return rendered;
  }

  return <AgentMessage>{rendered}</AgentMessage>;
}

interface ChatThreadProps {
  conversation: Conversation | null;
  connectionError?: string | null;
  onFocusNode?: (part: Extract<Part, { type: "node_ref" }>) => void;
}

export function ChatThread({
  conversation,
  connectionError,
  onFocusNode,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const pinnedRef = useRef(true);

  const messages = conversation?.messages ?? [];
  const items = buildThreadItems(messages);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    const onScroll = () => {
      const distance = el.scrollHeight - el.scrollTop - el.clientHeight;
      pinnedRef.current = distance < 40;
    };
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!pinnedRef.current) return;
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [items, connectionError]);

  return (
    <div
      ref={scrollerRef}
      className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto px-4 pt-4 pb-2"
      aria-label="Agent conversation"
    >
      {items.length === 0 ? (
        <p className="rounded-agent-card border border-agent-border-subtle bg-agent-bg-card px-3.5 py-3 text-[13px] text-agent-text-muted">
          Attach a node and ask about it, or ask for a walkthrough.
        </p>
      ) : (
        conversation &&
        items.map((item) => (
          <div key={item.key}>
            {renderThreadItem(item, conversation, onFocusNode)}
          </div>
        ))
      )}
      {connectionError ? (
        <p className="rounded-agent-card border border-agent-danger-border bg-agent-danger-bg px-3.5 py-3 text-[12px] text-agent-text-muted">
          Connection lost — reload to see where it got to.
        </p>
      ) : null}
      <div ref={bottomRef} />
    </div>
  );
}

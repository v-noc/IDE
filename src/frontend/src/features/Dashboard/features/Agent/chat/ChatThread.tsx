import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import type { Conversation, Message, Part } from "../stream/types";
import { findDecisionForTool, renderPart } from "./parts/registry";

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

function MessageBubble({
  message,
  messageIndex,
  conversation,
  onFocusNode,
}: {
  message: Message;
  messageIndex: number;
  conversation: Conversation;
  onFocusNode?: (part: Extract<Part, { type: "node_ref" }>) => void;
}) {
  const isUser = message.role === "user";
  const nodeRefs = message.parts.filter(
    (p): p is Extract<Part, { type: "node_ref" }> => p.type === "node_ref",
  );
  const bodyParts = message.parts.filter((p) => p.type !== "node_ref");

  return (
    <article
      className={cn(
        "rounded-md border border-border p-3",
        isUser ? "bg-muted/40" : "bg-background",
      )}
    >
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {isUser ? "you" : "agent"}
      </p>
      {nodeRefs.length > 0 ? (
        <div className="mb-2 flex flex-wrap gap-1.5">
          {nodeRefs.map((part, i) => (
            <span key={`${part.node_id}-${i}`}>
              {renderPart(part, { onFocusNode })}
            </span>
          ))}
        </div>
      ) : null}
      <div className="space-y-2">
        {bodyParts.map((part, index) => {
          const partIndex = message.parts.indexOf(part);
          const rendered = renderPart(part, {
            isStreaming: isPartStreaming(
              conversation,
              messageIndex,
              partIndex,
            ),
            onFocusNode,
            decisionForTool: (toolCallId) =>
              findDecisionForTool(message.parts, toolCallId),
          });
          if (rendered == null) return null;
          return (
            <div key={`${message.id}-${part.type}-${index}`}>{rendered}</div>
          );
        })}
      </div>
      {message.metadata?.error ? (
        <p className="mt-2 text-[11px] text-destructive">
          {message.metadata.error}
        </p>
      ) : null}
    </article>
  );
}

interface ChatThreadProps {
  conversation: Conversation | null;
  connectionError?: string | null;
  onFocusNode?: (part: Extract<Part, { type: "node_ref" }>) => void;
  className?: string;
}

export function ChatThread({
  conversation,
  connectionError,
  onFocusNode,
  className,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const pinnedRef = useRef(true);

  const messages = conversation?.messages ?? [];

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
  }, [messages]);

  return (
    <div
      ref={scrollerRef}
      className={cn("flex-1 space-y-3 overflow-auto p-4", className)}
    >
      {messages.length === 0 ? (
        <p className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
          Attach a node and ask about it, or ask for a walkthrough.
        </p>
      ) : (
        conversation &&
        messages.map((message, index) => (
          <MessageBubble
            key={message.id}
            message={message}
            messageIndex={index}
            conversation={conversation}
            onFocusNode={onFocusNode}
          />
        ))
      )}
      {connectionError ? (
        <p className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-xs text-muted-foreground">
          Connection lost — reload to see where it got to.
        </p>
      ) : null}
      <div ref={bottomRef} />
    </div>
  );
}

import type { WireMessage } from "@/types/agent";
import { cn } from "@/lib/utils";
import { MessageBubble } from "./MessageBubble";

export interface ChatContainerProps {
  messages: WireMessage[];
  streamingMessageIds: Set<string>;
  emptyLabel?: string;
  className?: string;
}

export function ChatContainer({
  messages,
  streamingMessageIds,
  emptyLabel = "No messages in this conversation.",
  className,
}: ChatContainerProps) {
  if (messages.length === 0) {
    return (
      <p
        className={cn(
          "rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground",
          className,
        )}
      >
        {emptyLabel}
      </p>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {messages.map((m) => (
        <MessageBubble
          key={m.id}
          message={m}
          streaming={streamingMessageIds.has(m.id)}
        />
      ))}
    </div>
  );
}

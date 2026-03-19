import type { MessageItemProps } from "./MessageItem";
import { MessageItem } from "./MessageItem";

export interface MessageListProps {
  messages: MessageItemProps[];
  emptyLabel?: string;
}

export function MessageList({
  messages,
  emptyLabel = "No messages in this conversation.",
}: MessageListProps) {
  if (messages.length === 0) {
    return (
      <p className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
        {emptyLabel}
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {messages.map((m) => (
        <MessageItem key={m.id} {...m} />
      ))}
    </div>
  );
}

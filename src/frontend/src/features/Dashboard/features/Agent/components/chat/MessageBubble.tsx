import { cn } from "@/lib/utils";
import type { WireMessage } from "@/types/agent";
import { wirePartType } from "./partTypes";
import { PartRenderer } from "./PartRenderer";

function firstTextPartIndex(parts: WireMessage["parts"]): number {
  return parts.findIndex((p) => wirePartType(p) === "text");
}

export interface MessageBubbleProps {
  message: WireMessage;
  streaming?: boolean;
  className?: string;
}

export function MessageBubble({ message, streaming, className }: MessageBubbleProps) {
  const textIdx = firstTextPartIndex(message.parts);

  return (
    <article
      className={cn(
        "rounded-md border border-border bg-muted/40 p-3",
        streaming && "border-primary/40",
        className,
      )}
    >
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {message.role}
        {streaming ? " · streaming" : ""}
      </p>
      <div className="flex flex-col gap-2">
        {message.parts.length === 0 ? (
          <p className="text-xs text-muted-foreground">No content.</p>
        ) : (
          message.parts.map((part, index) => (
            <PartRenderer
              key={`${message.id}-part-${index}`}
              part={part}
              role={message.role}
              streaming={streaming && index === textIdx}
            />
          ))
        )}
      </div>
    </article>
  );
}

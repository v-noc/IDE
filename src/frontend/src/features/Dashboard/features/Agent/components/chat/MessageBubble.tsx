import { cn } from "@/lib/utils";
import type { WireMessage } from "@/types/agent";
import { wirePartType } from "./partTypes";
import { PartRenderer } from "./PartRenderer";

function firstTextPartIndex(parts: WireMessage["parts"]): number {
  return parts.findIndex((p) => wirePartType(p) === "text");
}

function isUserRole(role: string): boolean {
  return role.toLowerCase() === "user";
}

export interface MessageBubbleProps {
  message: WireMessage;
  streaming?: boolean;
  className?: string;
}

export function MessageBubble({
  message,
  streaming,
  className,
}: MessageBubbleProps) {
  const textIdx = firstTextPartIndex(message.parts);
  const user = isUserRole(message.role);

  return (
    <div
      className={cn(
        "flex w-full min-w-0",
        user ? "justify-end" : "justify-start",
        className,
      )}
    >
      <article
        className={cn(
          "min-w-0  rounded-2xl px-3.5 py-2.5 ",
          user
            ? " text-black"
            : "rounded-bl-md border w-full border-border/80 bg-card text-card-foreground shadow-sm",
          streaming && !user && "ring-1 ring-primary/35",
        )}
      >
        <p
          className={cn(
            "mb-1.5 text-[10px] font-semibold uppercase tracking-wide",
            user ? "text-black/65 " : "text-muted-foreground",
          )}
        >
          {user ? "You" : message.role === "system" ? "System" : "Assistant"}
          {streaming && !user ? " · streaming" : ""}
        </p>
        <div className="flex flex-col gap-2.5">
          {message.parts.length === 0 ? (
            <p
              className={cn(
                "text-xs",
                user ? "text-primary-foreground/85" : "text-muted-foreground",
              )}
            >
              No content.
            </p>
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
    </div>
  );
}

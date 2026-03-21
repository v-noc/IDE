import { cn } from "@/lib/utils";
import type { WireMessage } from "@/types/agent";
import { AssistantMarkdown } from "./Markdown";
import { wireMessagePlainText } from "./wireText";

export interface MessageItemProps {
  id: string;
  role: string;
  text: string;
  streaming?: boolean;
  className?: string;
}

/** Normalized row for chat UI (wire or local fixture). */
export function MessageItem({
  id,
  role,
  text,
  streaming,
  className,
}: MessageItemProps) {
  return (
    <article
      className={cn(
        "rounded-md border border-border bg-muted/40 p-3",
        streaming && "border-primary/40",
        className,
      )}
    >
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
        {role}
        {streaming ? " · streaming" : ""}
      </p>
      {role === "assistant" ? (
        text || streaming ? (
          <AssistantMarkdown text={text || (streaming ? "…" : "")} />
        ) : (
          <p className="text-xs leading-relaxed text-muted-foreground">No text content.</p>
        )
      ) : (
        <p className="whitespace-pre-wrap text-xs leading-relaxed text-foreground">
          {text || (streaming ? "…" : "No text content.")}
        </p>
      )}
    </article>
  );
}

export function messageItemFromWire(
  m: WireMessage,
  opts?: { streaming?: boolean },
): MessageItemProps {
  return {
    id: m.id,
    role: m.role,
    text: wireMessagePlainText(m),
    streaming: opts?.streaming,
  };
}

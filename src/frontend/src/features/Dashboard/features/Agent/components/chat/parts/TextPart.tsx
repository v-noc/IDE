import type { WireTextPart } from "@/types/agent";
import { AssistantMarkdown } from "../../messages/Markdown";

export interface TextPartProps {
  part: WireTextPart;
  role: string;
  streaming?: boolean;
}

function markdownRole(role: string): boolean {
  const r = role.toLowerCase();
  return r === "assistant" || r === "system";
}

export function TextPart({ part, role, streaming }: TextPartProps) {
  const text = part.text;
  const isAssistant = markdownRole(role);

  if (isAssistant) {
    if (!text && !streaming) {
      return (
        <p className="text-xs leading-relaxed text-muted-foreground">
          No text content.
        </p>
      );
    }
    return (
      <div className="relative">
        <AssistantMarkdown text={text || (streaming ? "…" : "")} />
        {streaming && text ? (
          <span
            className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-primary align-middle"
            aria-hidden
          />
        ) : null}
      </div>
    );
  }

  return (
    <p className="whitespace-pre-wrap text-xs leading-relaxed text-black">
      {text || (streaming ? "…" : "No text content.")}
    </p>
  );
}

import { StepMarkdown } from "../../walkthrough/components/StepMarkdown";
import type { TextPart } from "../../stream/types";

export function TextPartView({
  part,
  isStreaming,
}: {
  part: TextPart;
  isStreaming?: boolean;
}) {
  if (!part.text.trim() && isStreaming) {
    return (
      <p className="animate-pulse text-xs text-muted-foreground">…</p>
    );
  }

  if (isStreaming) {
    // Avoid re-parsing markdown every token flush while the part is live.
    return (
      <p className="whitespace-pre-wrap text-xs leading-relaxed text-foreground">
        {part.text}
      </p>
    );
  }

  return (
    <div className="text-xs leading-relaxed text-foreground [&_p]:text-xs">
      <StepMarkdown text={part.text} />
    </div>
  );
}

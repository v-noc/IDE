import { StepMarkdown } from "../../walkthrough/components/StepMarkdown";
import type { TextPart } from "../../stream/types";

const proseClass =
  "text-[13.5px] leading-[1.6] text-agent-text-body [&_a]:text-agent-accent-link [&_a]:underline-offset-2 hover:[&_a]:text-agent-accent-text [&_p]:text-[13.5px] [&_p]:leading-[1.6]";

export function TextPartView({
  part,
  isStreaming,
}: {
  part: TextPart;
  isStreaming?: boolean;
}) {
  if (!part.text.trim() && isStreaming) {
    return <p className="animate-pulse text-[13.5px] text-agent-text-muted">…</p>;
  }

  if (isStreaming) {
    return (
      <p className={`whitespace-pre-wrap ${proseClass}`}>{part.text}</p>
    );
  }

  return (
    <div className={proseClass}>
      <StepMarkdown text={part.text} />
    </div>
  );
}

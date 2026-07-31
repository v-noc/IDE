import type { Message, NodeRefPart } from "../stream/types";
import { NodeRefChip } from "./parts/NodeRefChip";

interface UserMessageProps {
  message: Message;
  onFocusNode?: (part: NodeRefPart) => void;
}

export function UserMessage({ message, onFocusNode }: UserMessageProps) {
  const nodeRefs = message.parts.filter(
    (p): p is NodeRefPart => p.type === "node_ref",
  );
  const text = message.parts
    .filter((p) => p.type === "text")
    .map((p) => (p.type === "text" ? p.text : ""))
    .join("");

  return (
    <article className="shrink-0 rounded-agent-card border border-agent-border-subtle bg-agent-bg-card px-3.5 py-3">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <span className="text-[10.5px] font-bold tracking-[0.08em] text-agent-text-label">
          YOU
        </span>
        {nodeRefs.map((part) => (
          <NodeRefChip
            key={part.node_id}
            part={part}
            onFocus={onFocusNode}
          />
        ))}
      </div>
      {text ? (
        <p className="whitespace-pre-wrap text-[13.5px] leading-[1.55] text-agent-text">
          {text}
        </p>
      ) : null}
      {message.metadata?.error ? (
        <p className="mt-2 text-[11px] text-agent-danger">{message.metadata.error}</p>
      ) : null}
    </article>
  );
}

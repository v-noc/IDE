import { cn } from "@/lib/utils";
import type { NodeRefPart } from "../../stream/types";

export function NodeRefChip({
  part,
  onFocus,
  onRemove,
  className,
}: {
  part: NodeRefPart;
  onFocus?: (part: NodeRefPart) => void;
  onRemove?: () => void;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded-agent-pill border border-agent-border-strong bg-agent-bg-raised px-2 py-0.5 font-agent-mono text-[11px] text-agent-text-body",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => onFocus?.(part)}
        className="inline-flex max-w-full items-center gap-1.5 truncate"
        title={part.node_id}
      >
        <span
          className="size-1.5 shrink-0 rounded-sm bg-agent-text-muted"
          aria-hidden
        />
        <span className="truncate">{part.name}</span>
        <span className="text-agent-text-faint">{part.node_type}</span>
      </button>
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          className="shrink-0 text-agent-text-muted hover:text-agent-text"
          aria-label={`Remove ${part.name}`}
        >
          ×
        </button>
      ) : null}
    </span>
  );
}

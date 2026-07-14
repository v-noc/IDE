import { cn } from "@/lib/utils";
import type { NodeRefPart } from "../../stream/types";

export function NodeRefChipView({
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
        "inline-flex max-w-full items-center gap-1 rounded-md border border-border bg-muted/50 px-2 py-0.5 text-[11px] text-foreground",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => onFocus?.(part)}
        className="truncate hover:underline"
        title={part.node_id}
      >
        ⬡ {part.name}
        <span className="text-muted-foreground"> ({part.node_type})</span>
      </button>
      {onRemove ? (
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 text-muted-foreground hover:text-foreground"
          aria-label={`Remove ${part.name}`}
        >
          ✕
        </button>
      ) : null}
    </span>
  );
}

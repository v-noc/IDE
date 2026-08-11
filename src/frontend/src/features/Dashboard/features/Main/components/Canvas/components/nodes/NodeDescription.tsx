import { memo } from "react";

interface NodeDescriptionProps {
  description?: string;
  /** Fallback label when no description — e.g. "File main" */
  fallbackLabel?: string;
}

export const NodeDescription = memo(function NodeDescription({
  description,
  fallbackLabel,
}: NodeDescriptionProps) {
  const text = description?.trim() || fallbackLabel;

  return (
    <div className="px-3 py-3 text-[12.5px] leading-relaxed text-muted-foreground">
      {text ?? (
        <span className="italic opacity-70">No description available</span>
      )}
    </div>
  );
});

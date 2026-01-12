import { memo } from "react";

interface NodeDescriptionProps {
  description?: string;
}

export const NodeDescription = memo(function NodeDescription({
  description,
}: NodeDescriptionProps) {
  return (
    <div className="px-4 py-3.5 space-y-2.5 bg-white">
      {description ? (
        <p className="text-xs leading-relaxed text-slate-700">{description}</p>
      ) : (
        <div className="text-xs text-slate-400 italic">
          No description available
        </div>
      )}
    </div>
  );
});

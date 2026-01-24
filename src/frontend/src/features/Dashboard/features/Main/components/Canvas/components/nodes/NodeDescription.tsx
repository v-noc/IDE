import { memo } from "react";

interface NodeDescriptionProps {
  description?: string;
  textColor?: string;
}

export const NodeDescription = memo(function NodeDescription({
  description,
  textColor,
}: NodeDescriptionProps) {
  return (
    <div className="px-4 py-3.5 space-y-2.5 bg-whit/30">
      {description ? (
        <p className="text-xs leading-relaxed " style={{ color: textColor }}>{description}</p>
      ) : (
        <div className="text-xs text-slate-400 italic" style={{ color: textColor }}>
          No description available
        </div>
      )}
    </div>
  );
});

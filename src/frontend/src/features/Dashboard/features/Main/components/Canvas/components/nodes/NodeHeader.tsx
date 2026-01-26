import { memo, type ReactNode } from "react";
import { ChevronDown, ChevronRight, Code2 } from "lucide-react";

interface NodeHeaderProps {
  name: string;
  icon: ReactNode;
  iconColor: string;
  borderColor: string;
  textColor: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  hasCode?: boolean;
  showCode?: boolean;
  onCodeToggle?: () => void;
  status?: "error" | "warning" | "success" | "idle";
}

const statusColors: Record<string, string> = {
  error: "#ef4444",
  warning: "#f59e0b",
  success: "#10b981",
};

export const NodeHeader = memo(function NodeHeader({
  name,
  icon,
  iconColor,
  borderColor,
  textColor,
  expandable,
  expanded,
  onToggle,
  hasCode,
  showCode,
  onCodeToggle,
  status,
}: NodeHeaderProps) {
  return (
    <div
      className="flex items-center gap-3 border-b px-4 py-3.5 bg-slate-50/30"
      style={{ borderColor }}
    >
      {expandable && (
        <button
          onClick={() => {
            onToggle?.();
          }}
          className={`flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all hover:scale-110 ${
            expanded ? "bg-slate-200/5" : "bg-slate-100/15"
          }`}
          style={{
            borderColor,
          
          }}
        >
          {expanded ? (
            <ChevronDown size={18} style={{ color: iconColor }} />
          ) : (
            <ChevronRight size={18} style={{ color: iconColor }} />
          )}
        </button>
      )}

      <div className="flex items-center gap-2.5">
        <span className="text-xl" style={{ color: iconColor }}>
          {icon}
        </span>
        <span className="text-base font-bold tracking-wide text-slate-800" style={{ color: textColor }}>
          {name}
        </span>
      </div>

      <div className="flex-1" />

      {status && status !== "idle" && (
        <span
          className="h-3 w-3 rounded-full ring-2 ring-white"
          style={{ backgroundColor: statusColors[status] }}
        />
      )}

      {hasCode && (
        <button
          onClick={() => {
            onCodeToggle?.()
          }}
          className={`flex h-8 w-8 items-center justify-center rounded-lg border-2 transition-all hover:scale-110 ${
            showCode ? "bg-slate-200/5" : "bg-slate-100/15"
          }`}
          style={{
            borderColor,
            color: iconColor,
          }}
        >
          <Code2 size={16} style={{ color: iconColor }} />
        </button>
      )}
    </div>
  );
});

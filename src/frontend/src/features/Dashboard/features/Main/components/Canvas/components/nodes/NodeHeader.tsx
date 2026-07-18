import { memo, type ReactNode } from "react";
import { ChevronDown, ChevronRight, Code2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface NodeHeaderProps {
  name: string;
  icon: ReactNode;
  iconColor?: string;
  expandable?: boolean;
  expanded?: boolean;
  onToggle?: () => void;
  hasCode?: boolean;
  showCode?: boolean;
  onCodeToggle?: () => void;
  status?: "error" | "warning" | "success" | "idle";
  diffStatus?: "added" | "removed" | "modified" | null;
  taskOpenCount?: number;
  taskHot?: boolean;
  onTaskBadgeClick?: () => void;
}

const statusColors: Record<string, string> = {
  error: "bg-destructive",
  warning: "bg-chart-4",
  success: "bg-primary",
};

const diffColors: Record<string, { className: string; label: string }> = {
  added: {
    className: "border-primary/30 bg-primary/15 text-primary",
    label: "Added",
  },
  removed: {
    className: "border-destructive/30 bg-destructive/15 text-destructive",
    label: "Removed",
  },
  modified: {
    className: "border-chart-3/30 bg-chart-3/15 text-chart-3",
    label: "Updated",
  },
};

const iconBtnClass =
  "nodrag nopan flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-border bg-muted/60 text-primary transition-colors hover:bg-accent";

export const NodeHeader = memo(function NodeHeader({
  name,
  icon,
  iconColor,
  expandable,
  expanded,
  onToggle,
  hasCode,
  showCode,
  onCodeToggle,
  status,
  diffStatus,
  taskOpenCount,
  taskHot,
  onTaskBadgeClick,
}: NodeHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2.5">
      {expandable && (
        <button
          type="button"
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse subtree" : "Expand subtree"}
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            onToggle?.();
          }}
          className={iconBtnClass}
        >
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        </button>
      )}

      <div className="flex min-w-0 flex-1 items-center gap-2">
        <span
          className="text-lg text-primary [&_svg]:text-primary"
          style={iconColor ? { color: iconColor } : undefined}
        >
          {icon}
        </span>
        <span className="truncate text-sm font-semibold text-foreground">
          {name}
        </span>
        {taskOpenCount != null && taskOpenCount > 0 && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onTaskBadgeClick?.();
            }}
            className={cn(
              "nodrag nopan shrink-0 rounded-full border px-1.5 py-0.5 text-[10px] font-bold tabular-nums",
              taskHot
                ? "border-chart-4/40 bg-chart-4/15 text-chart-4"
                : "border-primary/35 bg-primary/10 text-primary",
            )}
          >
            {taskOpenCount}
          </button>
        )}
      </div>

      {status && status !== "idle" && (
        <span
          className={cn(
            "h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-card",
            statusColors[status],
          )}
        />
      )}

      {diffStatus && diffColors[diffStatus] && (
        <span
          className={cn(
            "shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide border",
            diffColors[diffStatus].className,
          )}
        >
          {diffColors[diffStatus].label}
        </span>
      )}

      {hasCode && (
        <button
          type="button"
          aria-label={showCode ? "Hide code" : "Show code"}
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            onCodeToggle?.();
          }}
          className={cn(iconBtnClass, showCode && "bg-accent")}
        >
          <Code2 size={15} />
        </button>
      )}
    </div>
  );
});

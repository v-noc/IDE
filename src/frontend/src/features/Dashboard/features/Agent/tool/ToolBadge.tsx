import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

export const toolBadgeVariants = cva(
  "rounded-agent-pill px-2 py-0.5 text-[10px] font-semibold tracking-[0.03em] whitespace-nowrap",
  {
    variants: {
      status: {
        queued: "bg-agent-bg-raised text-agent-text-muted",
        "needs approval":
          "border border-agent-warn-border bg-agent-warn-bg text-agent-warn",
        running:
          "border border-agent-accent-border-strong bg-agent-accent-bg-subtle text-agent-accent-text agent-tool-badge--pulse",
        done: "border border-agent-accent-border bg-agent-accent-bg-subtle text-agent-accent-text",
        error:
          "border border-agent-danger-border bg-agent-danger-bg text-agent-danger",
        cancelled: "bg-agent-bg-raised text-agent-text-muted",
      },
    },
    defaultVariants: {
      status: "queued",
    },
  },
);

export type ToolBadgeStatus = NonNullable<
  VariantProps<typeof toolBadgeVariants>["status"]
>;

interface ToolBadgeProps {
  status: ToolBadgeStatus;
  className?: string;
}

const LABELS: Record<ToolBadgeStatus, string> = {
  queued: "queued",
  "needs approval": "needs approval",
  running: "running",
  done: "done",
  error: "error",
  cancelled: "cancelled",
};

export function ToolBadge({ status, className }: ToolBadgeProps) {
  return (
    <span className={cn(toolBadgeVariants({ status }), className)}>
      {LABELS[status]}
    </span>
  );
}

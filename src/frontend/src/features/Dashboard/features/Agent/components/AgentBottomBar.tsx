import { cn } from "@/lib/utils";

interface AgentBottomBarProps {
  className?: string;
}

export function AgentBottomBar({ className }: AgentBottomBarProps) {
  return (
    <div
      className={cn(
        "pointer-events-auto rounded-xl border border-border bg-background p-3 text-foreground shadow-lg",
        className,
      )}
    >
      <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
        <span>01:15 / 03:45</span>
        <span>Thinking...</span>
      </div>

      <div className="mb-2 h-2 w-full rounded-full bg-muted">
        <div className="h-2 w-1/3 rounded-full bg-primary" />
      </div>

      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <button
          type="button"
          className="rounded-md border border-border bg-muted px-2 py-1 hover:bg-muted/80"
        >
          Play
        </button>
        <button
          type="button"
          className="rounded-md border border-border bg-muted px-2 py-1 hover:bg-muted/80"
        >
          Pause
        </button>
        <button
          type="button"
          className="rounded-md border border-border bg-muted px-2 py-1 hover:bg-muted/80"
        >
          Next
        </button>
      </div>
    </div>
  );
}

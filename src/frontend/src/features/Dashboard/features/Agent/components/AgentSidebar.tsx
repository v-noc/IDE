import { cn } from "@/lib/utils";

interface AgentSidebarProps {
  className?: string;
}

export function AgentSidebar({ className }: AgentSidebarProps) {
  return (
    <aside
      className={cn(
        "pointer-events-auto flex h-full w-full flex-col rounded-xl border border-border bg-background text-foreground shadow-lg",
        className,
      )}
    >
      <div className="border-b border-border px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          AI Cognitive Replay
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-auto p-4">
        <section className="rounded-md border border-border bg-muted/40 p-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Thought Stream
          </p>
          <ul className="space-y-1 text-xs text-foreground">
            <li>Analyzing dependencies...</li>
            <li>Identifying entry point...</li>
            <li>Focusing on selected node...</li>
          </ul>
        </section>

        <section className="rounded-md border border-border bg-muted/40 p-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Explanation
          </p>
          <p className="text-xs leading-relaxed text-foreground">
            Basic placeholder panel for agent explanations. Replace this with
            live stream and context when logic is added.
          </p>
        </section>
      </div>

      <div className="border-t border-border p-3">
        <div className="rounded-md border border-border bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
          Ask AI about this code...
        </div>
      </div>
    </aside>
  );
}

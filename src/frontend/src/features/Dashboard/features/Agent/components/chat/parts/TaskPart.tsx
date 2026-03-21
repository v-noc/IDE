import { ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

export interface TaskWirePart {
  type: "task";
  task_id: string;
  title: string;
  description?: string;
  state: string;
  progress?: number;
  workflow_name?: string;
}

function stateStyles(state: string): string {
  const s = state.toLowerCase();
  if (s.includes("complete") || s === "completed") {
    return "border-emerald-500/40 bg-emerald-500/5 text-emerald-700 dark:text-emerald-400";
  }
  if (s.includes("fail") || s.includes("error")) {
    return "border-destructive/40 bg-destructive/5 text-destructive";
  }
  if (s.includes("run") || s === "pending" || s.includes("progress")) {
    return "border-primary/40 bg-primary/5 text-primary";
  }
  return "border-border bg-muted/30 text-foreground";
}

export function TaskPart({ part }: { part: TaskWirePart }) {
  const pct =
    typeof part.progress === "number"
      ? Math.round(Math.min(100, Math.max(0, part.progress * 100)))
      : null;

  return (
    <div className={cn("rounded-md border p-2", stateStyles(part.state))}>
      <Collapsible defaultOpen className="group">
        <CollapsibleTrigger className="flex w-full items-start justify-between gap-2 text-left">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold leading-tight">{part.title}</p>
            {part.workflow_name ? (
              <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
                {part.workflow_name}
              </p>
            ) : null}
            {part.description ? (
              <p className="mt-1 text-[10px] leading-snug text-muted-foreground">
                {part.description}
              </p>
            ) : null}
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <span className="text-[10px] font-medium uppercase tracking-wide opacity-90">
              {part.state}
            </span>
            {pct !== null ? (
              <span className="font-mono text-[10px] text-muted-foreground">{pct}%</span>
            ) : null}
            <ChevronDown className="h-3.5 w-3.5 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
          </div>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <p className="mt-2 border-t border-border/60 pt-2 font-mono text-[10px] text-muted-foreground">
            task_id: {part.task_id}
          </p>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

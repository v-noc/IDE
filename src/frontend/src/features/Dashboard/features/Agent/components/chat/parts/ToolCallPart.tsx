import { ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";

export interface ToolCallWirePart {
  type: "tool_call";
  tool_name: string;
  tool_input: unknown;
  tool_output?: unknown;
}

function formatJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function ToolCallPart({ part }: { part: ToolCallWirePart }) {
  return (
    <div className="rounded-md border border-border bg-background/80 text-xs">
      <Collapsible defaultOpen={false} className="group">
        <CollapsibleTrigger className="flex w-full items-center justify-between gap-2 px-2 py-1.5 text-left font-medium text-foreground hover:bg-muted/50">
          <span className="truncate font-mono text-[11px]">{part.tool_name}</span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground transition-transform group-data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="space-y-2 border-t border-border px-2 py-2">
            <div>
              <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                Input
              </p>
              <pre className="max-h-40 overflow-auto rounded bg-muted/60 p-2 font-mono text-[10px] leading-snug">
                {formatJson(part.tool_input)}
              </pre>
            </div>
            {part.tool_output !== undefined ? (
              <div>
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Output
                </p>
                <pre
                  className={cn(
                    "max-h-48 overflow-auto rounded border border-border bg-muted/40 p-2 font-mono text-[10px] leading-snug",
                  )}
                >
                  {formatJson(part.tool_output)}
                </pre>
              </div>
            ) : null}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

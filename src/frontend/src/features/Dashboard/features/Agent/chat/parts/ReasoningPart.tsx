import { useMemo, useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { cn } from "@/lib/utils";
import type { ReasoningPart } from "../../stream/types";

function fmtSecs(durationMs: number | null | undefined): string {
  if (durationMs == null || durationMs < 0) return "a moment";
  const secs = Math.max(1, Math.round(durationMs / 1000));
  return `${secs}s`;
}

function lastLines(text: string, n: number): string {
  const lines = text.split("\n");
  if (lines.length <= n) return text;
  return lines.slice(-n).join("\n");
}

export function ReasoningPartView({
  part,
  isStreaming,
}: {
  part: ReasoningPart;
  isStreaming?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const label =
    part.origin === "summary" ? "Reasoning summary" : "Thinking";
  const liveText = useMemo(() => lastLines(part.text, 3), [part.text]);

  if (isStreaming) {
    return (
      <div className="rounded-md border border-border/60 bg-muted/30 px-2.5 py-2">
        <p className="mb-1 text-[11px] font-medium text-muted-foreground">
          <span className="animate-pulse">✧</span> {label}…
        </p>
        <p className="whitespace-pre-wrap text-[11px] leading-relaxed text-muted-foreground">
          {liveText || "…"}
        </p>
      </div>
    );
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger
        className={cn(
          "flex w-full items-center gap-1 rounded px-0.5 py-0.5 text-left text-[11px] text-muted-foreground transition hover:text-foreground",
        )}
      >
        <span aria-hidden>{open ? "▾" : "▸"}</span>
        Thought for {fmtSecs(part.duration_ms)}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <p className="mt-1 whitespace-pre-wrap border-l border-border pl-2 text-[11px] leading-relaxed text-muted-foreground">
          {part.text}
        </p>
      </CollapsibleContent>
    </Collapsible>
  );
}

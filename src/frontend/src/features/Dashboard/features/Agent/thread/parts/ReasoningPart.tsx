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
  const label = part.origin === "summary" ? "Reasoning summary" : "Thinking";
  const liveText = useMemo(() => lastLines(part.text, 3), [part.text]);

  if (isStreaming) {
    return (
      <div className="rounded-agent-field border border-agent-border bg-agent-bg-inset px-2.5 py-2">
        <p className="mb-1 font-agent-mono text-[11px] text-agent-text-muted">
          <span className="animate-pulse">◇</span> {label}…
        </p>
        <p className="whitespace-pre-wrap text-[11px] leading-relaxed text-agent-text-muted">
          {liveText || "…"}
        </p>
      </div>
    );
  }

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger
        className={cn(
          "flex w-full items-center gap-1 rounded px-0.5 py-0.5 text-left font-agent-mono text-[11px] text-agent-text-faint transition hover:text-agent-text-muted",
        )}
      >
        <span aria-hidden>{open ? "▾" : "▸"}</span>
        Thought for {fmtSecs(part.duration_ms)}
      </CollapsibleTrigger>
      <CollapsibleContent>
        <p className="mt-1 whitespace-pre-wrap rounded-agent-field border border-agent-border bg-agent-bg-inset px-2.5 py-2 text-[11px] leading-relaxed text-agent-text-muted">
          {part.text}
        </p>
      </CollapsibleContent>
    </Collapsible>
  );
}

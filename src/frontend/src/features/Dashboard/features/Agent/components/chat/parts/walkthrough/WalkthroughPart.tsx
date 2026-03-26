import { Map } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";
import type { WalkthroughWirePart } from "./types";

export function WalkthroughPart({ part }: { part: WalkthroughWirePart }) {
  const controls = useWalkthroughStore((s) => s.controls);
  const status = useWalkthroughStore((s) => s.status);
  const loadedId = useWalkthroughStore((s) => s.walkthrough?.meta.id);
  const isLoaded = loadedId === part.walkthrough.meta.id;
  const canStart = Boolean(controls);

  return (
    <div className="overflow-hidden rounded-lg border border-border bg-muted/25">
      <div className="flex gap-3 border-b border-border/60 px-3 py-2.5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-500/10 text-violet-700 dark:text-violet-300">
          <Map className="h-4 w-4" strokeWidth={2} aria-hidden />
        </div>
        <div className="min-w-0 flex-1 text-left">
          <p className="text-[13px] font-semibold leading-tight tracking-tight text-foreground">
            {part.title}
          </p>
          {part.description ? (
            <p className="mt-1 text-[11px] leading-snug text-muted-foreground">
              {part.description}
            </p>
          ) : null}
          {part.workflow_name ? (
            <p className="mt-1 font-mono text-[10px] text-muted-foreground/80">
              {part.workflow_name}
            </p>
          ) : null}
          <p className="mt-1 text-[10px] text-muted-foreground">
            {part.walkthrough.steps.length} step
            {part.walkthrough.steps.length === 1 ? "" : "s"} · Open the{" "}
            <span className="font-medium text-foreground">Canvas</span> tab,
            then play from the bar below.
          </p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 px-3 py-2">
        <Button
          type="button"
          size="sm"
          variant="default"
          disabled={!canStart}
          className={cn("h-8 text-xs", !canStart && "opacity-60")}
          onClick={() => void controls?.load(part.walkthrough)}
          title={
            canStart
              ? "Load this tour into the walkthrough player"
              : "Open a project canvas so the walkthrough engine is available"
          }
        >
          Load tour
        </Button>
        {isLoaded ? (
          <span className="text-[10px] text-muted-foreground tabular-nums">
            Player: {status}
          </span>
        ) : null}
      </div>
    </div>
  );
}

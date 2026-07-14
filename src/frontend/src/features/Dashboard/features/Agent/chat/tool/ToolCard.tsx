import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { DecisionPart, ToolPart } from "../../stream/types";
import { ConfirmCard } from "./ConfirmCard";
import { renderArtifact } from "../artifacts/registry";
import { useRunStream } from "../../hooks/useRunStream";

const TOOL_TITLES: Record<string, string> = {
  walkthrough: "Code walkthrough",
};

function statusLabel(status: string): string {
  switch (status) {
    case "pending":
      return "preparing";
    case "awaiting_confirmation":
      return "needs approval";
    case "running":
      return "running";
    case "completed":
      return "done";
    case "error":
      return "error";
    default:
      return status;
  }
}

interface ToolCardProps {
  part: ToolPart;
  decision?: DecisionPart | null;
}

export function ToolCard({ part, decision }: ToolCardProps) {
  const { stop, isStreaming } = useRunStream();
  const title = TOOL_TITLES[part.tool] ?? part.tool;
  const state = part.state;
  const degraded =
    state.status === "completed" && Boolean(state.degraded);

  return (
    <div className="overflow-hidden rounded-md border border-border bg-muted/20">
      <div className="flex items-center gap-2 border-b border-border/60 px-2.5 py-1.5">
        <span className="text-[11px] font-medium text-foreground">
          ⚙ {title}
        </span>
        <Badge variant="secondary" className="text-[10px]">
          {statusLabel(state.status)}
        </Badge>
        {degraded ? (
          <Badge variant="outline" className="text-[10px] text-amber-700">
            ⚠
          </Badge>
        ) : null}
      </div>

      <div className="space-y-2 p-2.5 text-xs">
        {state.status === "pending" ? (
          <p className="animate-pulse text-muted-foreground">Preparing…</p>
        ) : null}

        {state.status === "awaiting_confirmation" ? (
          <ConfirmCard
            part={part}
            estimate={state.estimate}
            input={state.input}
          />
        ) : null}

        {state.status === "running" ? (
          <div className="space-y-2">
            {state.progress ? (
              <>
                <div className="flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                  <span>{state.progress.label}</span>
                  <span>
                    {state.progress.done}/{state.progress.total}
                  </span>
                </div>
                <Progress
                  value={
                    state.progress.total > 0
                      ? (100 * state.progress.done) / state.progress.total
                      : 0
                  }
                />
              </>
            ) : (
              <p className="animate-pulse text-muted-foreground">Running…</p>
            )}
            {isStreaming ? (
              <div className="flex justify-end">
                <Button
                  type="button"
                  size="sm"
                  variant="secondary"
                  className="h-7 text-[11px]"
                  onClick={() => void stop()}
                >
                  Stop
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}

        {state.status === "completed" ? (
          <div className="space-y-2">
            <p className={cn("text-[11px] text-muted-foreground")}>
              {typeof state.result.stops === "number"
                ? `${state.result.stops} stops`
                : "Completed"}
              {typeof state.result.steps === "number"
                ? ` · ${state.result.steps} steps`
                : ""}
              {degraded ? " · fallback ⚠" : ""}
            </p>
            {state.artifact
              ? renderArtifact(state.artifact.render, state.artifact.doc)
              : null}
          </div>
        ) : null}

        {state.status === "error" ? (
          <p
            className={cn(
              "text-[11px]",
              state.error.includes("declined")
                ? "text-muted-foreground"
                : "text-amber-800 dark:text-amber-200",
            )}
          >
            {state.error.includes("declined")
              ? "cancelled — you declined"
              : state.error}
          </p>
        ) : null}

        {decision ? (
          <p className="border-t border-border/50 pt-2 text-[11px] text-muted-foreground">
            {decision.decision === "approve"
              ? `approved${
                  decision.overrides && Object.keys(decision.overrides).length
                    ? ` · ${Object.entries(decision.overrides)
                        .map(([k, v]) => `${k} ${v}`)
                        .join(" · ")}`
                    : ""
                }`
              : "declined"}
          </p>
        ) : null}
      </div>
    </div>
  );
}

import { AlertTriangle, Check, Link2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NodeSteps, VisitNode } from "../types";
import { blockStepId, firstStepIdForVisit } from "../store/flatten";

export type OutlineRowState = "pending" | "filled" | "done" | "degraded";

interface OutlineRowProps {
  visit: VisitNode;
  nodeSteps: NodeSteps | undefined;
  isCurrent: boolean;
  onJump: (stepId: string) => void;
  onJumpVisit: (order: number) => void;
}

function rowState(nodeSteps: NodeSteps | undefined): OutlineRowState {
  if (!nodeSteps || !nodeSteps.intro_text) return "pending";
  if (nodeSteps.degraded) return "degraded";

  const hasBlocks = nodeSteps.blocks.length > 0;
  if (!hasBlocks) return "filled";

  const allBlocksDone = nodeSteps.blocks.every((block) => block.text.length > 0);
  return allBlocksDone ? "done" : "filled";
}

function StatusIcon({ state }: { state: OutlineRowState }) {
  if (state === "done") {
    return <Check className="h-3 w-3 text-emerald-500" aria-hidden />;
  }
  if (state === "degraded") {
    return <AlertTriangle className="h-3 w-3 text-amber-500" aria-hidden />;
  }
  return (
    <span
      className="inline-block h-2 w-2 rounded-full bg-muted-foreground/40"
      aria-hidden
    />
  );
}

export function OutlineRow({
  visit,
  nodeSteps,
  isCurrent,
  onJump,
  onJumpVisit,
}: OutlineRowProps) {
  const state = rowState(nodeSteps);
  const isCall = visit.node_type === "call";
  const isContextual = visit.mode === "contextual";

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={() => onJump(firstStepIdForVisit(visit.order))}
        className={cn(
          "flex w-full items-start gap-2 rounded-md px-2 py-1.5 text-left text-xs transition hover:bg-muted/70",
          isCurrent && "border-l-2 border-primary bg-muted/50 pl-[6px]",
          state === "pending" && "text-muted-foreground",
        )}
        style={{ paddingLeft: `${8 + visit.level * 12}px` }}
      >
        <StatusIcon state={state} />
        <span className="min-w-0 flex-1">
          <span className="font-medium text-foreground">
            {isCall ? "↳ " : ""}
            {visit.name}
          </span>
          <span className="ml-1 text-[10px] text-muted-foreground">
            ({visit.node_type})
          </span>
          {isContextual && visit.first_seen_order != null ? (
            <button
              type="button"
              className="ml-2 inline-flex items-center gap-0.5 text-[10px] text-primary hover:underline"
              onClick={(event) => {
                event.stopPropagation();
                onJumpVisit(visit.first_seen_order!);
              }}
            >
              <Link2 className="h-3 w-3" />
              stop {visit.first_seen_order + 1}
            </button>
          ) : null}
        </span>
      </button>

      {nodeSteps?.blocks.map((block) => (
        <button
          key={block.index}
          type="button"
          onClick={() => onJump(blockStepId(visit.order, block.index))}
          className={cn(
            "flex w-full items-center gap-2 rounded-md py-1 text-left text-[11px] text-muted-foreground transition hover:bg-muted/50 hover:text-foreground",
            !block.text && "opacity-60",
          )}
          style={{ paddingLeft: `${24 + visit.level * 12}px` }}
        >
          <span className="text-[10px]">▸</span>
          <span className="truncate">{block.focus}</span>
        </button>
      ))}
    </div>
  );
}

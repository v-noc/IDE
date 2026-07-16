import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { cn } from "@/lib/utils";
import type { NodeSteps, VisitNode } from "../../../walkthrough/types";
import {
  blockStepId,
  firstStepIdForVisit,
} from "../../../walkthrough/store/flatten";
import { jumpToVisit, useWalkthroughStore } from "../../../walkthrough/store/useWalkthroughStore";

type OutlineMark = "check" | "dot" | "sub";

interface OutlineRowModel {
  key: string;
  label: string;
  kind?: string;
  depth: number;
  mark: OutlineMark;
  stopLabel?: string;
  visitOrder?: number;
  stepId?: string;
  isCurrent: boolean;
}

function rowMark(
  visit: VisitNode,
  nodeSteps: NodeSteps | undefined,
): OutlineMark {
  if (!nodeSteps?.intro_text) return "dot";
  if (nodeSteps.blocks.length > 0) return "check";
  return "dot";
}

function buildOutlineRows(
  visits: VisitNode[],
  stepsByOrder: Map<number, NodeSteps>,
  currentVisitOrder: number | null,
): OutlineRowModel[] {
  const rows: OutlineRowModel[] = [];

  visits.forEach((visit) => {
    const nodeSteps = stepsByOrder.get(visit.order);
    rows.push({
      key: `visit-${visit.order}`,
      label: visit.name,
      kind: visit.node_type,
      depth: visit.level,
      mark: rowMark(visit, nodeSteps),
      stopLabel:
        visit.mode === "contextual" && visit.first_seen_order != null
          ? `stop ${visit.first_seen_order + 1}`
          : undefined,
      visitOrder: visit.order,
      stepId: firstStepIdForVisit(visit.order),
      isCurrent: visit.order === currentVisitOrder,
    });

    nodeSteps?.blocks.forEach((block) => {
      rows.push({
        key: `block-${visit.order}-${block.index}`,
        label: block.focus,
        depth: visit.level + 1,
        mark: "sub",
        stepId: blockStepId(visit.order, block.index),
        isCurrent: false,
      });
    });
  });

  return rows;
}

function depthPadding(depth: number): string {
  if (depth <= 0) return "12px";
  if (depth === 1) return "28px";
  return "46px";
}

export function OutlineTree() {
  const [session, playerSteps, cursor, jumpTo] = useWalkthroughStore(
    useShallow((state) => [
      state.session,
      state.playerSteps,
      state.cursor,
      state.jumpTo,
    ]),
  );

  const currentVisitOrder = useMemo(() => {
    if (cursor < 0 || !playerSteps[cursor]) return null;
    return playerSteps[cursor].visitOrder;
  }, [cursor, playerSteps]);

  if (!session) return null;

  const stepsByOrder = new Map(
    session.node_steps.map((nodeSteps) => [nodeSteps.order, nodeSteps]),
  );
  const rows = buildOutlineRows(
    session.visit_list.nodes,
    stepsByOrder,
    currentVisitOrder,
  );

  return (
    <div className="overflow-hidden rounded-agent-field border border-agent-border-strong">
      <p className="px-3 pt-2.5 text-[10px] font-bold tracking-[0.08em] text-agent-text-label">
        TOUR OUTLINE
      </p>
      <div className="max-h-56 overflow-y-auto pb-1">
        {rows.map((row) => (
          <button
            key={row.key}
            type="button"
            onClick={() => {
              if (row.stepId) jumpTo(row.stepId);
              else if (row.visitOrder != null) jumpToVisit(row.visitOrder);
            }}
            className={cn(
              "flex w-full items-center gap-2 py-1.5 pr-3 text-left transition-colors hover:bg-agent-bg-raised/60",
              row.isCurrent && "bg-agent-accent-bg-subtle",
            )}
            style={{ paddingLeft: depthPadding(row.depth) }}
          >
            <span
              className={cn(
                "shrink-0",
                row.mark === "check" && "text-[11px] text-agent-text-agent-label",
                row.mark === "dot" && "text-[7px] text-agent-text-faint",
                row.mark === "sub" && "text-[9px] text-agent-text-faint",
              )}
              aria-hidden
            >
              {row.mark === "check" ? "✓" : row.mark === "sub" ? "▸" : "●"}
            </span>
            <span
              className={cn(
                "min-w-0 flex-1 truncate",
                row.mark === "sub"
                  ? "text-xs font-normal text-agent-text-muted"
                  : "text-[12.5px] font-semibold text-agent-text",
              )}
            >
              {row.label}
              {row.kind ? (
                <span className="ml-1 font-agent-mono text-[11px] font-normal text-agent-text-faint">
                  ({row.kind})
                </span>
              ) : null}
            </span>
            {row.stopLabel ? (
              <span className="shrink-0 text-xs font-semibold text-agent-accent-link">
                ⇢ {row.stopLabel}
              </span>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  );
}

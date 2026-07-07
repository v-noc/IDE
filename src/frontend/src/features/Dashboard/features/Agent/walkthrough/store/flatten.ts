import type { NodeSteps, VisitList, WalkthroughSession } from "../types";
import type { PlayerStep } from "../types";

function padOrder(order: number): string {
  return String(order).padStart(2, "0");
}

function visitName(visitList: VisitList, order: number): string {
  return visitList.nodes.find((n) => n.order === order)?.name ?? "stop";
}

function introStep(nodeSteps: NodeSteps, visitList: VisitList): PlayerStep {
  const orderKey = padOrder(nodeSteps.order);
  return {
    id: `n${orderKey}`,
    nodeId: nodeSteps.node_id,
    actions: [{ type: "select_node", nodeId: nodeSteps.node_id }],
    title: visitName(visitList, nodeSteps.order),
    text: nodeSteps.intro_text,
    degraded: nodeSteps.degraded,
    visitOrder: nodeSteps.order,
  };
}

function blockSteps(
  nodeSteps: NodeSteps,
  visitList: VisitList,
): PlayerStep[] {
  const orderKey = padOrder(nodeSteps.order);
  const steps: PlayerStep[] = [];

  nodeSteps.blocks.forEach((block, index) => {
    const actions =
      index === 0
        ? [
            { type: "show_code" as const, nodeId: nodeSteps.node_id },
            {
              type: "highlight_lines" as const,
              nodeId: nodeSteps.node_id,
              startLine: block.start_line,
              endLine: block.end_line,
            },
          ]
        : [
            {
              type: "highlight_lines" as const,
              nodeId: nodeSteps.node_id,
              startLine: block.start_line,
              endLine: block.end_line,
            },
          ];

    steps.push({
      id: `n${orderKey}.b${block.index}`,
      nodeId: nodeSteps.node_id,
      actions,
      title: block.focus,
      text: block.text,
      degraded: block.degraded || nodeSteps.degraded,
      visitOrder: nodeSteps.order,
    });
  });

  return steps;
}

function flattenNodeSteps(
  nodeSteps: NodeSteps,
  visitList: VisitList,
): PlayerStep[] {
  const intro = introStep(nodeSteps, visitList);

  if (nodeSteps.mode === "contextual" || nodeSteps.blocks.length === 0) {
    return [intro];
  }

  return [intro, ...blockSteps(nodeSteps, visitList)];
}

/**
 * Derives the executable step list from the session mirror.
 * Stable under growth: ids are keyed by visit order and block index only.
 */
export function flattenSession(session: WalkthroughSession): PlayerStep[] {
  const sorted = [...session.node_steps].sort((a, b) => a.order - b.order);
  return sorted.flatMap((nodeSteps) =>
    flattenNodeSteps(nodeSteps, session.visit_list),
  );
}

export function firstStepIdForVisit(order: number): string {
  return `n${padOrder(order)}`;
}

export function blockStepId(order: number, blockIndex: number): string {
  return `n${padOrder(order)}.b${blockIndex}`;
}

export function findStepIndex(
  steps: PlayerStep[],
  stepId: string,
): number {
  return steps.findIndex((step) => step.id === stepId);
}

import type { Edge, Node } from "@xyflow/react";
import type {
  DiffStatus,
  ParentChildDiff,
} from "../store/useVersioningStore";

type OverlayNodesResult = {
  nodes: Node[];
  nodeIds: Set<string>;
};

function withDiffStatus(node: Node, nodeDiffs: Record<string, DiffStatus>): Node {
  return {
    ...node,
    data: {
      ...(node.data as Record<string, unknown>),
      diffStatus: nodeDiffs[node.id] ?? null,
    },
  };
}

export function buildDiffOverlayNodes(
  initialNodes: Node[],
  currentNodes: Node[],
  parentChildDiffs: Record<string, ParentChildDiff>,
  nodeDiffs: Record<string, DiffStatus>
): OverlayNodesResult {
  const currentNodeMap = new Map(currentNodes.map((n) => [n.id, n]));

  const mergedNodes = initialNodes.map((newNode) => {
    const existingNode = currentNodeMap.get(newNode.id);
    if (existingNode) {
      return withDiffStatus(
        {
          ...existingNode,
          position: newNode.position,
          data: {
            ...(existingNode.data as Record<string, unknown>),
            ...(newNode.data as Record<string, unknown>),
          },
        },
        nodeDiffs
      );
    }
    return withDiffStatus(newNode, nodeDiffs);
  });

  if (Object.keys(parentChildDiffs).length === 0) {
    return { nodes: mergedNodes, nodeIds: new Set(mergedNodes.map((n) => n.id)) };
  }

  const mergedNodeMap = new Map(mergedNodes.map((n) => [n.id, n]));
  for (const diff of Object.values(parentChildDiffs)) {
    const childIds = [...diff.added, ...diff.removed];
    for (const childId of childIds) {
      if (mergedNodeMap.has(childId)) continue;
      const existingNode = currentNodeMap.get(childId);
      if (!existingNode) continue;
      mergedNodeMap.set(childId, withDiffStatus(existingNode, nodeDiffs));
    }
  }

  const nodes = [...mergedNodeMap.values()];
  return { nodes, nodeIds: new Set(nodes.map((n) => n.id)) };
}

export function buildDiffOverlayEdges(
  initialEdges: Edge[],
  parentChildDiffs: Record<string, ParentChildDiff>,
  nodeIds: Set<string>
): Edge[] {
  if (Object.keys(parentChildDiffs).length === 0) {
    return initialEdges;
  }

  const edgeMap = new Map(initialEdges.map((edge) => [edge.id, edge]));
  for (const [parentId, diff] of Object.entries(parentChildDiffs)) {
    const childIds = [...diff.added, ...diff.removed];
    for (const childId of childIds) {
      if (!nodeIds.has(parentId) || !nodeIds.has(childId)) continue;
      const edgeId = `${parentId}-${childId}`;
      if (edgeMap.has(edgeId)) continue;
      edgeMap.set(edgeId, {
        id: edgeId,
        source: parentId,
        target: childId,
        type: "bezier",
      });
    }
  }

  return [...edgeMap.values()];
}

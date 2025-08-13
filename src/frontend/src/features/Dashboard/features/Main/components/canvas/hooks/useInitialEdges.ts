import { useMemo } from "react";
import type { Edge, Node } from "@xyflow/react";

export function useInitialEdges(initialNodes: Node[]): Edge[] {
    return useMemo((): Edge[] => {
        if (!initialNodes || initialNodes.length === 0) return [];
        const startNode = initialNodes.find((n) => n.type === "circle" && n.id.startsWith("__start__"));
        const endNode = initialNodes.find((n) => n.type === "circle" && n.id.startsWith("__end__"));
        const dataNodes = initialNodes
            .filter((n) => n.type !== "circle")
            .sort((a, b) => (a.position?.x ?? 0) - (b.position?.x ?? 0));

        const sequenceIds: string[] = [];
        if (startNode) sequenceIds.push(startNode.id);
        sequenceIds.push(...dataNodes.map((n) => n.id));
        if (endNode) sequenceIds.push(endNode.id);

        const edges: Edge[] = [];
        for (let i = 0; i < sequenceIds.length - 1; i++) {
            const source = sequenceIds[i];
            const target = sequenceIds[i + 1];
            edges.push({ id: `e-${source}-${target}`, source, target, type: "smartEdge" });
        }
        return edges;
    }, [initialNodes]);
}



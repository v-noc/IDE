import { useCallback, useMemo } from "react";
import { addEdge, type Edge, type Node, type Connection, type OnConnect } from "@xyflow/react";

export function useCanvasGraph(projectId?: string) {
    const initialNodes = useMemo<Node[]>(
        () => [
            {
                id: "1",
                type: "codeNode",
                position: { x: 250, y: 0 },
                data: { label: `Entry (${projectId ?? "no-id"})` },
            },
            {
                id: "2",
                type: "docNode",
                position: { x: 100, y: 150 },
                data: { label: "Docs" },
            },
        ],
        [projectId]
    );

    const initialEdges = useMemo<Edge[]>(
        () => [
            { id: "e1-2", source: "1", target: "2", type: "smartEdge" },
        ],
        []
    );

    const onNodesChange = useCallback(() => {
        // placeholder for external node state handling
    }, []);

    const onEdgesChange = useCallback(() => {
        // placeholder for external edge state handling
    }, []);

    const onConnect = useCallback(
        (setEdges: (updater: Edge[] | ((eds: Edge[]) => Edge[])) => void): OnConnect =>
            (connection: Connection) =>
                setEdges((eds) => addEdge({ ...connection, type: "smartEdge" }, eds)),
        []
    );

    return { initialNodes, initialEdges, onNodesChange, onEdgesChange, onConnect };
}



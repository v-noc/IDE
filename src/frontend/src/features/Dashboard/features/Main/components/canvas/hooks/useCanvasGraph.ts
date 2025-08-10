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
            {
                id: "fn-1",
                type: "functionNode",
                position: { x: 450, y: 150 },
                data: {
                    name: "helper_function",
                    qname: "app.utils.helper_function",
                    inputs: [
                        { name: "i", type: "int" },
                        { name: "b", type: "Optional[bool]" },
                    ],
                    outputs: [{ name: "return", type: "str" }],
                    callOrder: 1,
                    performance: { avgTime: 0.5, runCount: 12, successRate: 1 },
                    isExpanded: true,
                },
            },
            {
                id: "cls-1",
                type: "classNode",
                position: { x: 250, y: 320 },
                data: {
                    name: "User",
                    qname: "models.user.User",
                    fields: [
                        { name: "name", type: "str" },
                        { name: "age", type: "int" },
                    ],
                    methods: [
                        { name: "__init__" },
                        { name: "get_name", returnType: "str" },
                    ],
                    sourceFile: "models/user.py",
                    isExpanded: true,
                },
            },
        ],
        [projectId]
    );

    const initialEdges = useMemo<Edge[]>(
        () => [
            { id: "e1-2", source: "1", target: "2", type: "smartEdge" },
            { id: "e1-fn", source: "1", target: "fn-1", type: "smartEdge" },
            { id: "e2-cls", source: "2", target: "cls-1", type: "smartEdge" },
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



import { useCallback } from "react";
import { addEdge, type Edge, type Connection, type OnConnect } from "@xyflow/react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useSelectedFromSources } from "./useSelectedFromSources";
import { useInitialNodes } from "./useInitialNodes";
import { useInitialEdges } from "./useInitialEdges";

export function useCanvasGraph(projectId?: string) {
    const { projectData } = useProjectStore();
    const projectKey = projectId || projectData?.id || "";
    const selectedNode = useProjectStore((s) => s.selectedNode);

    const selectedFromSources = useSelectedFromSources(projectKey);
    const initialNodes = useInitialNodes(selectedFromSources);
    const initialEdges = useInitialEdges(initialNodes);

    const onNodesChange = useCallback(() => { }, []);
    const onEdgesChange = useCallback(() => { }, []);

    const onConnect = useCallback(
        (setEdges: (updater: Edge[] | ((eds: Edge[]) => Edge[])) => void): OnConnect =>
            (connection: Connection) => setEdges((eds) => addEdge({ ...connection, type: "smartEdge" }, eds)),
        []
    );

    return {
        initialNodes,
        doNotReRenderCanvas: selectedNode?.doNotReRenderCanvas,
        initialEdges,
        selected: selectedFromSources.node,
        parent: selectedFromSources.parent,
        onNodesChange,
        onEdgesChange,
        onConnect,
    };
}
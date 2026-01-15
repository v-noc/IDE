import { useCallback } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { findNodeByFunctionId, findPathToNode } from "@/features/Dashboard/utils/treeUtils";
import type { LogNode } from "@/services/logs/api";

/**
 * Hook to reveal and focus a node in the Canvas based on log selection.
 */
export const useNodeRevealer = () => {
    const {
        selectedNode,
        expandedNodeIds,
        expandNode,
        setFocusTargetId
    } = useProjectStore();

    const revealNode = useCallback((targetLogNode: LogNode, rootLogNode: LogNode) => {
        if (!selectedNode || !targetLogNode.function_id || !rootLogNode.function_id) {
            return;
        }

        // We only proceed if the current canvas selection matches the trace root.
        const selectedKey = selectedNode._id.split("/").pop();
        const rootKey = rootLogNode.function_id.split("/").pop();

        if (selectedKey !== rootKey) {
            return;
        }

        // Search within the CURRENTLY SELECTED tree scope.
        const targetCanvasNode = findNodeByFunctionId(selectedNode, targetLogNode.function_id);

        if (!targetCanvasNode) {
            console.warn("[useNodeRevealer] Target node not found in current selection tree", targetLogNode.function_id);
            return;
        }

        // Find path from selection root to target
        const path = findPathToNode(selectedNode, targetCanvasNode._id);


        if (path) {
            path.forEach(id => {
                if (!expandedNodeIds.includes(id)) {
                    // Collect key after the last slash
                    const key = id.includes("/") ? id.split("/").pop()! : id;
                    expandNode(key);
                }
            });

            // Set focus target for CanvasView to react
            setFocusTargetId(targetCanvasNode._id);
        }
    }, [selectedNode, expandedNodeIds, expandNode, setFocusTargetId]);

    return { revealNode };
};

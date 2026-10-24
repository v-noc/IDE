import { useCallback } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { findNodeByFunctionId, findPathToNode } from "@/features/Dashboard/utils/treeUtils";
import type { LogNode } from "@/services/logs/api";
import type { AnyNodeTree, CallNodeTree } from "@/types/project";

// Mirrors useLogsState's effective-node logic: the Logs panel fetches logs for
// secondarySelectedNode when present (falling back to selectedNode), so the trace
// root a log row belongs to is scoped to that same node, not always the primary one.
function toEffectiveNode(
    selectedNode: AnyNodeTree | null | undefined,
    secondarySelectedNode: AnyNodeTree | null | undefined
) {
    if (secondarySelectedNode) {
        if ((secondarySelectedNode as CallNodeTree).target) {
            return (secondarySelectedNode as CallNodeTree).target;
        }
        return secondarySelectedNode;
    }
    if (selectedNode?.node_type === "call") {
        return (selectedNode as CallNodeTree).target;
    }
    return selectedNode;
}

/**
 * Hook to reveal and focus a node in the Canvas based on log selection.
 */
export const useNodeRevealer = (tabId: string) => {
    const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
    const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode[tabId]);
    const effectiveNode = toEffectiveNode(selectedNode, secondarySelectedNode);
    const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds[tabId] ?? []);
    const expandNodesBulk = useProjectStore((s) => s.expandNodesBulk);
    const handleNodeSelection = useTabStore((s) => s.handleNodeSelection);

    const revealNode = useCallback((targetLogNode: LogNode, rootLogNode: LogNode) => {
        if (!effectiveNode || !targetLogNode.function_id || !rootLogNode.function_id) {
            return;
        }

        // We only proceed if the node the logs are scoped to matches the trace root.
        const selectedKey = effectiveNode.id.split("/").pop();
        const rootKey = rootLogNode.function_id.split("/").pop();

        if (selectedKey !== rootKey) {
            return;
        }

        // Search within the tree scope the logs are currently showing.
        const targetCanvasNode = findNodeByFunctionId(effectiveNode, targetLogNode.function_id);

        if (!targetCanvasNode) {
            console.warn("[useNodeRevealer] Target node not found in current selection tree", targetLogNode.function_id);
            return;
        }

        // Find path from selection root to target
        const path = findPathToNode(effectiveNode, targetCanvasNode.id);


        if (path) {
            // Canvas/sidebar match on full node ids, so expand with the full id.
            const toExpand = path.filter(id => !expandedNodeIds.includes(id));
            if (toExpand.length) {
                expandNodesBulk(tabId, toExpand);
            }

            // Highlight the target node on canvas only - must not disturb
            // selectedNode/secondarySelectedNode, which is what the Logs (and
            // Code/Docs/Playground) panels filter/scope their content by. Using
            // "secondary" here would re-scope those panels to the clicked log
            // row's node, causing the log list to refilter out from under the user.
            handleNodeSelection(tabId, targetCanvasNode, "highlight");
        }
    }, [effectiveNode, expandedNodeIds, expandNodesBulk, handleNodeSelection, tabId]);

    return { revealNode };
};

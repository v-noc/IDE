import { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { CallNodeTree } from "@/types/project";

import type { ProjectStore } from "@/features/Dashboard/store/useProjectStore";

/**
 * Derived state for the Workspace.
 * Handles node resolution, path display, and active content detection.
 */
export function useWorkspaceState(tabId: string) {
    const selectedNode = useProjectStore((s: ProjectStore) => s.selectedNode[tabId]);
    const secondarySelectedNode = useProjectStore((s: ProjectStore) => s.secondarySelectedNode[tabId]);
    const selectedDocumentId = useProjectStore((s: ProjectStore) => s.selectedDocumentId[tabId]);

    const effectiveNode = useMemo(() => {
        if (secondarySelectedNode) {
            if ((secondarySelectedNode as CallNodeTree).target) {
                return (secondarySelectedNode as CallNodeTree).target;
            }
            return secondarySelectedNode;
        }
        if (selectedNode?.node_type === "call") {
            return selectedNode.target;
        }
        return selectedNode;
    }, [secondarySelectedNode, selectedNode]);

    const displayPath = useMemo(() => {
        return effectiveNode?.qname?.replace(/\./g, " / ") ?? "";
    }, [effectiveNode]);

    const isCodeActive = useMemo(() => {
        const t = effectiveNode?.node_type;
        return t === "function" || t === "class" || t === "file" || t === "call";
    }, [effectiveNode?.node_type]);

    return {
        effectiveNode,
        displayPath,
        isCodeActive,
        selectedDocumentId,
        selectedNode,
        secondarySelectedNode,
    };
}

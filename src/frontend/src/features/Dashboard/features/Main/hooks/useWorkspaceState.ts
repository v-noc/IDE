import { useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { CallNodeTree } from "@/types/project";

/**
 * Derived state for the Workspace.
 * Handles node resolution, path display, and active content detection.
 */
export function useWorkspaceState() {
    const {
        selectedNode,
        secondarySelectedNode,
        selectedDocumentId,
    } = useProjectStore();

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

    const { suffixName, displayPath } = useMemo(() => {
        const base = selectedNode?.qname?.replace(/\./g, " / ") ?? "";
        const hasSuffix = Boolean(
            secondarySelectedNode && secondarySelectedNode._key !== selectedNode?._key
        );
        const suffix = hasSuffix ? secondarySelectedNode?.name ?? "" : "";
        const display = hasSuffix ? (base ? `${base} / ${suffix}` : suffix) : base;
        return { suffixName: suffix, displayPath: display };
    }, [selectedNode?.qname, selectedNode?._key, secondarySelectedNode]);

    const isCodeActive = useMemo(() => {
        const t = effectiveNode?.node_type;
        return t === "function" || t === "class" || t === "file" || t === "call";
    }, [effectiveNode?.node_type]);

    return {
        effectiveNode,
        displayPath,
        suffixName,
        isCodeActive,
        selectedDocumentId,
    };
}

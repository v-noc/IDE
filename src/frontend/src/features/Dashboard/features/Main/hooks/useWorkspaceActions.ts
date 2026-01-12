import { useCallback, useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useUpdateDocument } from "@/features/Dashboard/features/Main/service/useDocuments";
import { debounce } from "remeda";

/**
 * Mutation actions for the Workspace.
 * Handles node promotion and document content updates.
 */
export function useWorkspaceActions() {
    const {
        selectedNode,
        secondarySelectedNode,
        setSelectedNode,
        setSecondarySelectedNode,
    } = useProjectStore();

    const handlePromote = useCallback(() => {
        if (secondarySelectedNode) {
            setSelectedNode(secondarySelectedNode);
            setSecondarySelectedNode(null);
        }
    }, [secondarySelectedNode, setSelectedNode, setSecondarySelectedNode]);

    const updateMutation = useUpdateDocument(selectedNode?._key || "");

    const updateDocumentDebounced = useMemo(
        () =>
            debounce(
                (payload: { id: string; data: string }) => {
                    updateMutation.mutate({ id: payload.id, data: payload.data });
                },
                { waitMs: 1000 }
            ),
        [updateMutation]
    );

    return {
        handlePromote,
        updateDocumentDebounced,
    };
}

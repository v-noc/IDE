import { useEffect, useEffectEvent, useMemo } from "react";
import { debounce } from "remeda";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { type CallNodeTree } from "@/types/project";
import { useGetDocuments, useUpdateDocument } from "../service/useDocuments";

/**
 * Hook to manage document state and sync logic for a workspace tab.
 * Uses React 19 rules and useEffectEvent for non-reactive logic.
 */
export function useWorkspaceDocs(tabId: string, effectiveNode: any, selectedNode: any, secondarySelectedNode: any) {
    const selectedDocumentId = useProjectStore((s) => s.selectedDocumentId[tabId]);
    const setSelectedDocumentId = useProjectStore((s) => s.setSelectedDocumentId);

    const nodeKey = effectiveNode?._key || "";
    const { data: documents = [] } = useGetDocuments(nodeKey);

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

    const selectedDocument = useMemo(
        () => documents.find((d) => d._key === selectedDocumentId) || null,
        [documents, selectedDocumentId]
    );

    // Sync effect - wrapped logic in useEffectEvent to isolate non-reactive parts
    const syncDocumentSelection = useEffectEvent(() => {
        const currentSelected = secondarySelectedNode
            ? (secondarySelectedNode as CallNodeTree)?.target ?? selectedNode
            : selectedNode;

        if (
            (!selectedDocumentId ||
                !currentSelected?.documents.includes(`documents/${selectedDocumentId}`)) &&
            documents.length > 0
        ) {
            setSelectedDocumentId(tabId, documents[0]._key);
        }
    });

    useEffect(() => {
        syncDocumentSelection();
    }, [tabId, documents, selectedNode, secondarySelectedNode]);

    const handleDocumentChange = (data: string) => {
        if (selectedDocumentId) {
            updateDocumentDebounced.call({
                id: selectedDocumentId,
                data,
            });
        }
    };

    const selectDocument = (id: string) => {
        setSelectedDocumentId(tabId, id);
    };

    return {
        documents,
        selectedDocumentId,
        selectedDocument,
        handleDocumentChange,
        selectDocument,
    };
}

import { useEffect, useEffectEvent, useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { type CallNodeTree } from "@/types/project";
import { useDocuments } from "@/services/documents";

/**
 * Hook to manage document fetching and selection state for a workspace tab.
 * 
 * Responsibilities:
 * - Fetch documents for the effective node
 * - Manage selected document ID in global store
 * - Sync selection when node changes
 * 
 * Note: Document editing, saving, and API calls are handled by DocumentEditor component.
 * Uses React 19 rules and useEffectEvent for non-reactive logic.
 */
export function useWorkspaceDocs(
  tabId: string,
  effectiveNode: any,
  selectedNode: any,
  secondarySelectedNode: any
) {
  const selectedDocumentId = useProjectStore((s) => s.selectedDocumentId[tabId]);
  const setSelectedDocumentId = useProjectStore((s) => s.setSelectedDocumentId);
  const projectId = useProjectStore((s) => s.projectData?.id);

  const nodeKey = effectiveNode?.id || "";
  const { data: documents = [] } = useDocuments(nodeKey, projectId ?? undefined);

  const selectedDocument = useMemo(
    () => documents.find((d) => d.id === selectedDocumentId) || null,
    [documents, selectedDocumentId]
  );

  // Sync document selection when node changes
  // Wrapped logic in useEffectEvent to isolate non-reactive parts
  const syncDocumentSelection = useEffectEvent(() => {
    const currentSelected = secondarySelectedNode
      ? (secondarySelectedNode as CallNodeTree)?.target ?? selectedNode
      : selectedNode;

    // Get current node key for comparison
    const currentNodeKey = currentSelected?.id || "";

    // If no node is selected, clear document selection
    if (!currentSelected) {
      if (selectedDocumentId) {
        setSelectedDocumentId(tabId, null);
      }
      return;
    }

    // Check if selected document belongs to current node
    const documentBelongsToNode = selectedDocumentId
      ? currentSelected?.documents?.includes(`documents/${selectedDocumentId}`)
      : false;

    // If we have documents and either:
    // - No document is selected, OR
    // - Selected document doesn't belong to current node
    if (documents.length > 0) {
      if (!selectedDocumentId || !documentBelongsToNode) {
        setSelectedDocumentId(tabId, documents[0].id);
      }
    } else {
      // No documents available, clear selection
      if (selectedDocumentId) {
        setSelectedDocumentId(tabId, null);
      }
    }
  });

  useEffect(() => {
    syncDocumentSelection();
  }, [tabId, documents, selectedNode?.id, secondarySelectedNode?.id, syncDocumentSelection]);

  const selectDocument = (id: string) => {
    setSelectedDocumentId(tabId, id);
  };

  return {
    documents,
    selectedDocumentId,
    selectedDocument,
    nodeKey,
    projectId,
    selectDocument,
  };
}

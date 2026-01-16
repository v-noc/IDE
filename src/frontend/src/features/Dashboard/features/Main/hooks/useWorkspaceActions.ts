import { useCallback, useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useUpdateDocument } from "@/features/Dashboard/features/Main/service/useDocuments";
import { debounce } from "remeda";

/**
 * Mutation actions for the Workspace.
 * Handles node promotion and document content updates.
 */
export function useWorkspaceActions(tabId: string) {
  const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
  const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode[tabId]);
  const handleNodeSelection = useTabStore((s) => s.handleNodeSelection);
  const setSecondarySelectedNode = useProjectStore((s) => s.setSecondarySelectedNode);

  const handlePromote = useCallback(() => {
    if (secondarySelectedNode) {
      console.log("handlePromote", tabId, secondarySelectedNode);
      handleNodeSelection(tabId, secondarySelectedNode);
      setSecondarySelectedNode(tabId, null);
    }
  }, [secondarySelectedNode, tabId, handleNodeSelection, setSecondarySelectedNode]);

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

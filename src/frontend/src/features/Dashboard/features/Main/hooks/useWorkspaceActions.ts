import { useCallback } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";

/**
 * Mutation actions for the Workspace.
 * Handles node promotion and document content updates.
 */
export function useWorkspaceActions(tabId: string) {
  const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode[tabId]);
  const handleNodeSelection = useTabStore((s) => s.handleNodeSelection);
  const setSecondarySelectedNode = useProjectStore((s) => s.setSecondarySelectedNode);

  const handlePromote = useCallback(() => {
    if (secondarySelectedNode) {
      if (secondarySelectedNode.node_type === "call") {

        handleNodeSelection(tabId, secondarySelectedNode.target, "promte");
        setSecondarySelectedNode(tabId, null);
      } else {
        handleNodeSelection(tabId, secondarySelectedNode, "promte");
        setSecondarySelectedNode(tabId, null);
      }

    }
  }, [secondarySelectedNode, tabId, handleNodeSelection, setSecondarySelectedNode]);

  return {
    handlePromote,
  };
}

import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useLogTree } from "@/services/logs";
import { useParams } from "react-router";
import type { AnyNodeTree, CallNodeTree } from "@/types/project";

// Canvas clicks on a node that isn't already the focused/center node select it as
// "secondary" (a preview, without promoting it to the focused node) rather than
// "primary". Code/Docs/Playground all prefer secondarySelectedNode over selectedNode
// for exactly this reason - mirror that here so canvas selection filters logs too.
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
 * Hook to manage the state and data fetching for logs.
 * Now uses the global consolidated logs service.
 */
export function useLogsState(tabId: string) {
  const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
  const secondarySelectedNode = useProjectStore(
    (s) => s.secondarySelectedNode[tabId]
  );
  const effectiveNode = toEffectiveNode(selectedNode, secondarySelectedNode);
  const { projectId } = useParams();
  const nodeId = effectiveNode?.id || "";

  const { data: logs, isLoading } = useLogTree(nodeId, "ProjectSchema/" + projectId);

  return {
    logs: logs ?? [],
    isLoading,
    hasSelection: !!effectiveNode,
    nodeType: effectiveNode?.node_type,
  };
}

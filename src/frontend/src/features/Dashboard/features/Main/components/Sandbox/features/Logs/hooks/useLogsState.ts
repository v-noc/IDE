import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useLogTree } from "@/services/logs";

/**
 * Hook to manage the state and data fetching for logs.
 * Now uses the global consolidated logs service.
 */
export function useLogsState() {
    const { selectedNode } = useProjectStore();
    const nodeId = selectedNode?._key || "";

    const { data: logs, isLoading } = useLogTree(nodeId);

    return {
        logs: logs ?? [],
        isLoading,
        hasSelection: !!selectedNode,
        nodeType: selectedNode?.node_type,
    };
}

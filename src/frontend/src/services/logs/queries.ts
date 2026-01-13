import { useQuery } from '@tanstack/react-query';
import queryKeys from '@/lib/queryKeys';
import { logsApi, type LogTreeNode } from './api';

/**
 * Fetch log tree for any node.
 * Used by: Canvas nodes, Logs Sidebar, Right Panel
 */
export const useLogTree = (nodeId: string | undefined) => {
  return useQuery<LogTreeNode[]>({
    queryKey: queryKeys.logs.tree(nodeId ?? ''),
    queryFn: () => logsApi.getLogTree(nodeId!),
    enabled: !!nodeId,
    staleTime: 30 * 1000, // 30 seconds (logs update frequently)
  });
};

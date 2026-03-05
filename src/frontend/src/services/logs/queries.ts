import { useQuery } from '@tanstack/react-query';
import queryKeys from '@/lib/queryKeys';
import { logsApi, type LogTreeNode } from './api';

/**
 * Fetch log tree for any node.
 * Used by: Canvas nodes, Logs Sidebar, Right Panel
 */
export const useLogTree = (functionId: string, projectId: string) => {
  return useQuery<LogTreeNode[]>({
    queryKey: queryKeys.logs.tree(functionId, projectId),
    queryFn: () => logsApi.getLogTree(functionId, projectId),
    enabled: !!functionId && !!projectId,
    staleTime: 30 * 1000, // 30 seconds (logs update frequently)
  });
};

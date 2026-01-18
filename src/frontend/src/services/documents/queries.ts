import { useQuery } from "@tanstack/react-query";
import { documentsApi, type DocumentData } from "./api";
import queryKeys from "@/lib/queryKeys";

/**
 * Fetch documents for a node.
 * Used by: Document Editor, Right Sidebar, Doc Sidebar
 * All consumers share the same cache!
 */
export const useDocuments = (nodeId: string | undefined) => {
  return useQuery<DocumentData[]>({
    queryKey: queryKeys.documents.list(nodeId ?? ''),
    queryFn: () => documentsApi.getDocuments(nodeId!),
    enabled: !!nodeId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};


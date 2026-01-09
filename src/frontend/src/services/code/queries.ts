import { useQuery } from "@tanstack/react-query";
import { codeApi, type CodeData } from "./api";
import queryKeys from "@/lib/queryKeys";

/**
 * Fetch code for any node.
 * Used by: Canvas nodes, Code Editor, Right Panel
 * All consumers share the same cache!
 */
export const useCode = (elementId: string | undefined) => {
  return useQuery<CodeData>({
    queryKey: queryKeys.code.detail(elementId ?? ''),
    queryFn: () => codeApi.getCode(elementId!),
    enabled: !!elementId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

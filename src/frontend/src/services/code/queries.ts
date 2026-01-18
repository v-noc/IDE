import { useQuery } from "@tanstack/react-query";
import { codeApi, type CodeData } from "./api";
import queryKeys from "@/lib/queryKeys";

/**
 * Valid node types that support code.
 */
const VALID_CODE_NODE_TYPES = ["file", "function", "class", "call"] as const;
type ValidCodeNodeType = typeof VALID_CODE_NODE_TYPES[number];

/**
 * Fetch code for a node.
 * Only works for: file, function, class, call node types.
 * Used by: Canvas nodes, Code Editor, Right Panel
 * All consumers share the same cache!
 */
export const useCode = (
  elementId: string | undefined,
  nodeType?: string
) => {
  // Validate node type if provided
  const isValidNodeType =
    !nodeType || VALID_CODE_NODE_TYPES.includes(nodeType as ValidCodeNodeType);

  return useQuery<CodeData>({
    queryKey: queryKeys.code.detail(elementId ?? ''),
    queryFn: () => codeApi.getCode(elementId!),
    enabled: !!elementId && isValidNodeType,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

import queryKeys from "@/lib/queryKeys";
import { codeApi } from "@/services/code/api";
import type { AnyNodeTree, NodeType } from "@/types/project";

export const LAZY_CODE_CONTAINER_TYPES = new Set<NodeType>([
  "file",
  "class",
  "function",
  "call",
  "group",
]);

export function canLazyLoadCodeChildren(
  node: Pick<AnyNodeTree, "node_type" | "id"> & {
    lazy_child_ids?: string[];
  },
): boolean {
  const hint = node.lazy_child_ids?.length ?? 0;
  return (
    LAZY_CODE_CONTAINER_TYPES.has(node.node_type) && hint > 0
  );
}

export function getCodeDescendantsQueryOptions(
  projectId: string,
  parentId: string,
  branch: string | null | undefined,
  ref: string | null | undefined,
  compareTo: string | null | undefined,
) {
  return {
    queryKey: queryKeys.code.descendants(
      projectId,
      parentId,
      branch,
      ref,
      compareTo,
    ),
    queryFn: () =>
      codeApi.getDescendants(projectId, parentId, {
        depthStart: 1,
        depthMax: 4,
        compareTo,
      }),
  };
}

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import queryKeys from "@/lib/queryKeys";
import { codeApi } from "@/services/code/api";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";


const LAZY_NODE_TYPES = new Set([
  "file",
  "class",
  "function",
  "call",
  "group",
]);

/**
 * Load direct code children (depth 1–1) as a nested tree; cached by react-query.
 */
export function useLazyCodeChildren(
  node: ContainerNodeTree,
  isOpen: boolean
) {
  const projectId = useProjectStore((s) => s.projectData?.id ?? "");
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const hint = node.lazy_child_ids?.length ?? 0;
  const canLazy =
    LAZY_NODE_TYPES.has(node.node_type) && hint > 0 && !!projectId;

  const enabled = isOpen && canLazy;

  const query = useQuery({
    queryKey: queryKeys.code.descendants(
      projectId,
      node.id,
      branch,
      ref,
      compareTo
    ),
    queryFn: () =>
      codeApi.getDescendants(projectId, node.id, {
        depthStart: 1,
        depthMax: 4,
        compareTo,
      }),
    enabled,
  });

  const loadedNodes = useMemo((): AnyNodeTree[] => {
    const roots = query.data?.children;
    if (!roots?.length) return [];
    return roots as unknown as AnyNodeTree[];
  }, [query.data]);

  return {
    loadedNodes,
    isFetching: query.isFetching,
  };
}

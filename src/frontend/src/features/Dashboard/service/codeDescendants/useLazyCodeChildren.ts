import { useMemo } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";

import queryKeys from "@/lib/queryKeys";
import { codeApi } from "@/services/code/api";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { ContainerNodeTree } from "@/types/project";

import { CODE_DESCENDANTS_PAGE_SIZE } from "./constants";
import { normalizeCodeDescendant } from "./normalizeDescendantNode";

const LAZY_NODE_TYPES = new Set([
  "file",
  "class",
  "function",
  "call",
  "group",
]);

/**
 * Paginated direct code children (depth 1) for nodes with backend lazy_child_ids.
 * Cached by react-query; does not write to the project store.
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

  const query = useInfiniteQuery({
    queryKey: queryKeys.code.descendants(
      projectId,
      node.id,
      branch,
      ref,
      compareTo
    ),
    initialPageParam: 0,
    queryFn: async ({ pageParam }) =>
      codeApi.getDescendants(projectId, node.id, {
        depthStart: 1,
        depthMax: 1,
        limit: CODE_DESCENDANTS_PAGE_SIZE,
        offset: pageParam as number,
        compareTo,
      }),
    getNextPageParam: (lastPage, allPages) =>
      lastPage.has_next_page
        ? allPages.reduce((sum, p) => sum + p.nodes.length, 0)
        : undefined,
    enabled,
  });

  const loadedNodes = useMemo(() => {
    if (!query.data?.pages.length) return [];
    return query.data.pages.flatMap((page) =>
      page.nodes.map((n) => normalizeCodeDescendant(n))
    );
  }, [query.data]);

  return {
    loadedNodes,
    hasNextPage: query.hasNextPage,
    isFetching: query.isFetching,
    fetchNextPage: query.fetchNextPage,
  };
}

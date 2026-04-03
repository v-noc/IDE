import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";

import {
  canLazyLoadCodeChildren,
  getCodeDescendantsQueryOptions,
} from "./codeDescendantsQuery";

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

  const canLazy = canLazyLoadCodeChildren(node) && !!projectId;

  const enabled = isOpen && canLazy;

  const query = useQuery({
    ...getCodeDescendantsQueryOptions(
      projectId,
      node.id,
      branch,
      ref,
      compareTo,
    ),
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

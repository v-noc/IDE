import type { InfiniteData, QueryClient } from "@tanstack/react-query";

import { normalizeCodeDescendant } from "@/features/Dashboard/service/codeDescendants/normalizeDescendantNode";
import queryKeys from "@/lib/queryKeys";
import type { CodeDescendantsResponse } from "@/services/code/api";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

import { findNodeByKey } from "./findNode";

/**
 * Resolve a node from the structure tree, or from any cached `code.descendants` infinite query for this project.
 */
export function findNodeByIdWithDescendantCache(
  queryClient: QueryClient,
  structureRoot: ProjectNodeTree | null,
  projectKey: string,
  id: string,
): AnyNodeTree | null {
  if (!id) return null;
  const fromStructure = findNodeByKey(structureRoot, id);
  if (fromStructure) return fromStructure;
  if (!projectKey) return null;

  const codeRoot = queryKeys.code.all[0];
  const queries = queryClient.getQueryCache().findAll({
    predicate: (q) => {
      const k = q.queryKey as readonly unknown[];
      return (
        k.length >= 4 &&
        k[0] === codeRoot &&
        k[1] === "descendants" &&
        k[2] === projectKey
      );
    },
  });

  for (const q of queries) {
    const data = q.state.data as
      | InfiniteData<CodeDescendantsResponse>
      | undefined;
    if (!data?.pages?.length) continue;
    for (const page of data.pages) {
      for (const raw of page.nodes) {
        const n = normalizeCodeDescendant(raw);
        if (n.id === id) return n as AnyNodeTree;
      }
    }
  }
  return null;
}

import type { QueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import type { CodeDescendantsResponse } from "@/services/code/api";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

import { findNodeByKey } from "./findNode";

function rawNodeId(raw: Record<string, unknown>): string {
  const id = raw.id ?? raw["@id"];
  return typeof id === "string" ? id : "";
}

function findInDescendantForest(
  roots: Record<string, unknown>[],
  targetId: string,
): AnyNodeTree | null {
  for (const raw of roots) {
    if (rawNodeId(raw) === targetId) {
      return raw as unknown as AnyNodeTree;
    }
    const ch = raw.children;
    if (Array.isArray(ch)) {
      const objs = ch.filter(
        (x): x is Record<string, unknown> =>
          x != null && typeof x === "object" && !Array.isArray(x),
      );
      const hit = findInDescendantForest(objs, targetId);
      if (hit) return hit;
    }
    const t = raw.target;
    if (t && typeof t === "object" && !Array.isArray(t)) {
      const hit = findInDescendantForest([t as Record<string, unknown>], targetId);
      if (hit) return hit;
    }
  }
  return null;
}

/**
 * Resolve a node from the structure tree, or from any cached `code.descendants` query for this project.
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
    const data = q.state.data as CodeDescendantsResponse | undefined;
    if (!data?.children?.length) continue;
    const hit = findInDescendantForest(
      data.children as Record<string, unknown>[],
      id,
    );
    if (hit) return hit;
  }
  return null;
}

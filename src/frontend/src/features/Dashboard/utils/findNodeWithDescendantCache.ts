import type { QueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { canLazyLoadCodeChildren } from "@/features/Dashboard/service/codeDescendants";
import type { CodeDescendantsResponse } from "@/services/code/api";
import type { AnyNodeTree, ContainerNodeTree, ProjectNodeTree } from "@/types/project";

import { findNodeByKey } from "./findNode";
import { mergeStructureAndLazyChildren } from "./mergeCodeTreeChildren";

function rawNodeId(raw: Record<string, unknown>): string {
  const id = raw.id ?? raw["@id"];
  return typeof id === "string" ? id : "";
}

export function findInDescendantForest(
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

function getEffectiveChildrenMerged(
  queryClient: QueryClient,
  projectKey: string,
  branch: string | null | undefined,
  ref: string | null | undefined,
  compareTo: string | null | undefined,
  node: ContainerNodeTree,
): AnyNodeTree[] {
  const structure = (node.children ?? []) as AnyNodeTree[];
  if (!projectKey) return structure;
  if (
    !canLazyLoadCodeChildren(
      node as unknown as Parameters<typeof canLazyLoadCodeChildren>[0],
    )
  ) {
    return structure;
  }
  const data = queryClient.getQueryData<CodeDescendantsResponse>(
    queryKeys.code.descendants(projectKey, node.id, branch, ref, compareTo),
  );
  const loaded = (data?.children ?? []) as unknown as AnyNodeTree[];
  return mergeStructureAndLazyChildren(structure, loaded);
}

/**
 * Parent of `node` when traversing structure plus cached `code.descendants` merges (same as sidebar tree).
 */
export function getParentNodeWithDescendantCache(
  node: AnyNodeTree,
  root: ContainerNodeTree,
  queryClient: QueryClient,
  projectKey: string,
  branch: string | null | undefined,
  ref: string | null | undefined,
  compareTo: string | null | undefined,
): ContainerNodeTree | null {
  const effective = getEffectiveChildrenMerged(
    queryClient,
    projectKey,
    branch,
    ref,
    compareTo,
    root,
  );
  if (effective.some((c) => c.id === node.id)) {
    return root;
  }
  for (const child of effective) {
    const sub = getParentNodeWithDescendantCache(
      node,
      child as ContainerNodeTree,
      queryClient,
      projectKey,
      branch,
      ref,
      compareTo,
    );
    if (sub) return sub;
  }
  return null;
}

/**
 * Siblings of `node` under the resolved parent (structure + lazy descendants merged).
 */
export function getSiblingsWithDescendantCache(
  node: AnyNodeTree,
  root: ContainerNodeTree,
  queryClient: QueryClient,
  projectKey: string,
  branch: string | null | undefined,
  ref: string | null | undefined,
  compareTo: string | null | undefined,
): AnyNodeTree[] {
  const parent = getParentNodeWithDescendantCache(
    node,
    root,
    queryClient,
    projectKey,
    branch,
    ref,
    compareTo,
  );
  if (!parent) return [];
  const effective = getEffectiveChildrenMerged(
    queryClient,
    projectKey,
    branch,
    ref,
    compareTo,
    parent,
  );
  return effective.filter((c) => c.id !== node.id);
}

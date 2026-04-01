import type { QueryClient } from '@tanstack/react-query';

import { useVersioningStore } from '@/features/Dashboard/features/Versioning/store/useVersioningStore';
import queryKeys from '@/lib/queryKeys';
import { codeApi, type CodeDescendantsResponse } from '@/services/code/api';
import type { AnyNodeTree, ProjectNodeTree } from '@/types/project';

import { findNodeByKey } from './findNode';
import {
  findInDescendantForest,
  findNodeByIdWithDescendantCache,
} from './findNodeWithDescendantCache';

type NodeWithChildren = AnyNodeTree & { children?: AnyNodeTree[] };

const LAZY_LINEAGE_PARENT_TYPES = new Set([
  'file',
  'class',
  'function',
  'call',
  'group',
]);

function findChildInLoadedTree(
  parent: AnyNodeTree,
  childId: string,
): AnyNodeTree | null {
  const ch = (parent as NodeWithChildren).children;
  if (!Array.isArray(ch)) return null;
  for (const c of ch) {
    if (c?.id === childId) return c;
  }
  return null;
}

/**
 * Walk ``pathIds`` (root → leaf) using structure children only, fetching code
 * descendants when a lazy parent has no loaded child for the next id.
 */
export async function resolveLineageFromPath(
  queryClient: QueryClient,
  structureRoot: ProjectNodeTree | null,
  projectKey: string,
  pathIds: string[],
): Promise<AnyNodeTree[] | null> {
  if (!structureRoot || pathIds.length === 0 || !projectKey) return null;

  const vs = useVersioningStore.getState();
  const branch = vs.branch;
  const ref = vs.checkedOutCommitId;
  const compareTo = vs.compareToCommitId;

  const resolved: AnyNodeTree[] = [];
  let parent: AnyNodeTree | null = null;

  for (let i = 0; i < pathIds.length; i++) {
    const stepId = pathIds[i];
    let node: AnyNodeTree | null = null;

    if (i === 0) {
      node =
        structureRoot.id === stepId
          ? structureRoot
          : findNodeByKey(structureRoot, stepId);
    } else if (parent) {
      node = findChildInLoadedTree(parent, stepId);

      if (
        !node &&
        LAZY_LINEAGE_PARENT_TYPES.has(parent.node_type as string)
      ) {
        const qk = queryKeys.code.descendants(
          projectKey,
          parent.id,
          branch,
          ref,
          compareTo,
        );
        await queryClient.fetchQuery({
          queryKey: qk,
          queryFn: () =>
            codeApi.getDescendants(projectKey, parent!.id, {
              depthStart: 1,
              depthMax: 4,
              compareTo,
            }),
        });
        const cached = queryClient.getQueryData<CodeDescendantsResponse>(qk);
        const roots = cached?.children as Record<string, unknown>[] | undefined;
        if (roots?.length) {
          node = findInDescendantForest(roots, stepId);
        }
        if (!node) {
          node = findChildInLoadedTree(parent, stepId);
        }
      }
    }

    if (!node) {
      node = findNodeByIdWithDescendantCache(
        queryClient,
        structureRoot,
        projectKey,
        stepId,
      );
    }

    if (!node) return null;
    resolved.push(node);
    parent = node;
  }

  return resolved;
}

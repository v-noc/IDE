import type { QueryClient } from "@tanstack/react-query";
import { codeApi } from "@/services/code/api";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { findNodeByIdWithDescendantCache } from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import { resolveLineageFromPath } from "@/features/Dashboard/utils/resolveLineageFromPath";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

export interface EnsureOnCanvasOptions {
  /** When true, re-root via focus stack (call-portal flow). Default false. */
  reroot?: boolean;
}

/**
 * Ensures a node exists on the canvas, injecting ancestors via lineage when needed.
 * With `reroot: false` (default), expansion only — no focus or primary selection writes.
 */
export async function ensureOnCanvas(
  queryClient: QueryClient,
  tabId: string,
  nodeId: string,
  opts: EnsureOnCanvasOptions = {},
): Promise<AnyNodeTree | null> {
  const { reroot = false } = opts;
  const projectData = useProjectStore.getState().projectData;
  const projectKey = projectData?.id ?? "";
  if (!projectKey || !projectData) return null;

  const cached = findNodeByIdWithDescendantCache(
    queryClient,
    projectData,
    projectKey,
    nodeId,
  );
  if (cached) return cached;

  try {
    const { path_ids } = await codeApi.getLineage(projectKey, nodeId);
    if (!path_ids?.length) return null;

    const lineage = await resolveLineageFromPath(
      queryClient,
      projectData as ProjectNodeTree,
      projectKey,
      path_ids,
    );
    if (!lineage?.length) return null;

    const store = useProjectStore.getState();
    const lineageIds = lineage.map((node) => node.id);

    if (reroot) {
      store.clearFocus(tabId);
      store.pushFocusBulk(tabId, lineage);
      store.expandNodesBulk(tabId, lineageIds);
    } else {
      store.expandNodesBulk(tabId, lineageIds);
    }

    return lineage[lineage.length - 1];
  } catch {
    return null;
  }
}

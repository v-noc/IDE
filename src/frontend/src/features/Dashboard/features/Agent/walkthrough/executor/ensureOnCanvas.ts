import type { QueryClient } from "@tanstack/react-query";
import { codeApi } from "@/services/code/api";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { findNodeByIdWithDescendantCache } from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import { resolveLineageFromPath } from "@/features/Dashboard/utils/resolveLineageFromPath";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

/**
 * Ensures a node exists on the canvas, injecting ancestors via lineage when needed.
 * Mirrors the call-portal / deep-link focus flow.
 */
export async function ensureOnCanvas(
  queryClient: QueryClient,
  tabId: string,
  nodeId: string,
): Promise<AnyNodeTree | null> {
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
    store.clearFocus(tabId);
    store.pushFocusBulk(tabId, lineage);
    store.expandNodesBulk(
      tabId,
      lineage.map((node) => node.id),
    );

    return lineage[lineage.length - 1];
  } catch {
    return null;
  }
}

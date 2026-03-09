import { useEffect, useEffectEvent, useMemo } from "react";
import { useParams } from "react-router-dom";

import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { applyNodeDiffStatus } from "@/features/Dashboard/features/Versioning/utils/applyNodeDiffStatus";
import { useTreeFilter } from "./useTreeFilter";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

const STRUCTURAL_NODE_TYPES = new Set([
  "project",
  "folder",
  "file",
  "class",
  "function",
  "call",
  "group",
]);

export function useSidebarData() {
  const { projectId } = useParams();

  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNodeByTab = useProjectStore((s) => s.selectedNode);
  const secondarySelectedNodeByTab = useProjectStore((s) => s.secondarySelectedNode);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  const setProjectData = useProjectStore((s) => s.setProjectData);
  const rawProjectData = useProjectStore((s) => s.projectData);

  const isVersioningOpen = useVersioningStore((s) => s.isOpen);
  const selectedCommitId = useVersioningStore((s) => s.selectedCommitId);
  const historyScopeByTab = useVersioningStore((s) => s.historyScopeByTab);
  const diffResult = useVersioningStore((s) => s.diffResult);
  const activeScope = historyScopeByTab[activeTabId];
  const activeNode =
    secondarySelectedNodeByTab[activeTabId] ?? selectedNodeByTab[activeTabId];
  const isStructuralScope =
    activeScope?.scopeType === "canvas" &&
    activeNode?.node_type != null &&
    STRUCTURAL_NODE_TYPES.has(activeNode.node_type);
  const commitRef = isVersioningOpen && isStructuralScope ? selectedCommitId : undefined;
  const projectKey = "ProjectSchema/" + projectId || "";

  const { data, isLoading, isSuccess } = useGetProjectTreeWithKeyProject({
    key: projectKey,
    ref: commitRef ?? undefined,
  });

  /*
   * Sync server data to store.
   * Uses useEffectEvent to avoid reactive cycle with projectData.
   */
  const syncProjectData = useEffectEvent((newData: AnyNodeTree) => {
    setProjectData(newData as ProjectNodeTree);
    // Check expansion logic (also accesses latest state via closure/event)
    if (projectId && activeTabId && !expandedNodeIds[activeTabId]?.includes(projectId)) {
      toggleNodeExpansion(activeTabId, projectId);
    }
  });

  useEffect(() => {
    if (data && isSuccess) {
      const treeWithDiff = applyNodeDiffStatus(
        data as ProjectNodeTree,
        isVersioningOpen ? diffResult : null,
      );
      if (treeWithDiff) {
        syncProjectData(treeWithDiff);
      }
    }
  }, [data, isSuccess, isVersioningOpen, diffResult]); // eslint-disable-line react-hooks/exhaustive-deps

  // Tree Filtering
  const { filteredNodes, searchQuery, setSearchQuery } = useTreeFilter(
    rawProjectData?.children as AnyNodeTree[]
  );

  // Derived filtered project data
  const filteredProjectData = useMemo(() => {
    if (!rawProjectData) return null;
    return {
      ...rawProjectData,
      children: filteredNodes
    } as AnyNodeTree;
  }, [rawProjectData, filteredNodes]);

  return {
    isLoading,
    rawProjectData,
    filteredProjectData,
    searchQuery,
    setSearchQuery,
  };
}

import { useEffect, useEffectEvent, useMemo } from "react";
import { useParams } from "react-router-dom";

import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { useTreeFilter } from "./useTreeFilter";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

export function useSidebarData() {
  const { projectId } = useParams();

  const activeTabId = useTabStore((s) => s.activeTabId);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  const setProjectData = useProjectStore((s) => s.setProjectData);
  const rawProjectData = useProjectStore((s) => s.projectData);

  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const headCommitId = useVersioningStore((s) => s.headCommitId);
  const setHeadCommitId = useVersioningStore((s) => s.setHeadCommitId);
  const projectKey = projectId ? `ProjectSchema/${projectId}` : "";

  const { data, isLoading, isSuccess } = useGetProjectTreeWithKeyProject({
    key: projectKey,
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
    if (!checkedOutCommitId && data?.version && headCommitId !== data.version) {
      setHeadCommitId(data.version);
    }
  }, [checkedOutCommitId, data?.version, headCommitId, setHeadCommitId]);

  useEffect(() => {
    if (data && isSuccess) {
      syncProjectData(data as ProjectNodeTree);
    }
  }, [data, isSuccess]); // eslint-disable-line react-hooks/exhaustive-deps

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

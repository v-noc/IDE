import { useEffect, useEffectEvent, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useTreeFilter } from "./useTreeFilter";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

/**
 * Hook to manage sidebar data:
 * - Fetches project tree data based on route params.
 * - Synchronizes server data with the project store.
 * - Integrates tree filtering logic.
 */
export function useSidebarData() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();

  const { data, isLoading, isSuccess } =
    useGetProjectTreeWithKeyProject({
      key: projectId || "",
    });

  const setProjectData = useProjectStore((s) => s.setProjectData);
  const rawProjectData = useProjectStore((s) => s.projectData);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  const activeTabId = useTabStore((s) => s.activeTabId);

  /*
   * Sync server data to store.
   * Uses useEffectEvent to avoid reactive cycle with projectData.
   */
  const syncProjectData = useEffectEvent((newData: AnyNodeTree) => {
    // Only update if referentially different
    if (newData !== rawProjectData) {
      setProjectData(newData as ProjectNodeTree);
    }
    // Check expansion logic (also accesses latest state via closure/event)
    if (projectId && activeTabId && !expandedNodeIds[activeTabId]?.includes(projectId)) {
      toggleNodeExpansion(activeTabId, projectId);
    }
  });

  useEffect(() => {
    if (data && isSuccess) {
      syncProjectData(data);
    }
  }, [data, isSuccess]); // Only run when server data actually changes/arrives



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

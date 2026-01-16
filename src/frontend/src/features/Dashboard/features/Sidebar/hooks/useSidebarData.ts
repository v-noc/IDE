import { useEffect, useEffectEvent, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useTreeFilter } from "./useTreeFilter";
import type { AnyNodeTree } from "@/types/project";

/**
 * Hook to manage sidebar data:
 * - Fetches project tree data based on route params.
 * - Synchronizes server data with the project store.
 * - Handles cache invalidation on "code-saved" events.
 * - Integrates tree filtering logic.
 */
export function useSidebarData() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();

  const { data, isLoading, isSuccess, dataUpdatedAt } =
    useGetProjectTreeWithKeyProject({
      key: projectId || "",
    });

  const { setProjectData, projectData: rawProjectData, expandedNodeIds, toggleNodeExpansion } = useProjectStore();

  const ensureProjectExpanded = useEffectEvent(() => {
    if (projectId && !expandedNodeIds.includes(projectId)) {
      toggleNodeExpansion(projectId);
    }
  });

  // Sync server data to store
  useEffect(() => {
    if (data && isSuccess) {
      setProjectData(data);
      ensureProjectExpanded()
    }
  }, [data, setProjectData, isSuccess, dataUpdatedAt]);

  // Listen for code saves to invalidate query
  useEffect(() => {
    const handler = () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectId] });
    };
    window.addEventListener("code-saved", handler);
    return () => window.removeEventListener("code-saved", handler);
  }, [projectId, queryClient]);

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

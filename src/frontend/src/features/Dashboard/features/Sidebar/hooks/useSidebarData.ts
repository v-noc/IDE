import { useEffect, useEffectEvent, useMemo } from "react";
import { useParams } from "react-router-dom";

import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import { useTreeFilter } from "./useTreeFilter";
import type { AnyNodeTree, ProjectNodeTree } from "@/types/project";

function normalizeCommitId(commitId?: string | null): string | null {
  if (!commitId) return null;
  return commitId.startsWith("branch:") ? commitId.slice("branch:".length) : commitId;
}

const AFFECTED_STATUSES = new Set(["added", "removed", "modified"]);

function filterAffectedTree(nodes: AnyNodeTree[]): AnyNodeTree[] {
  return nodes.reduce<AnyNodeTree[]>((acc, node) => {
    const children = "children" in node ? (node.children as AnyNodeTree[]) : [];
    const filteredChildren = filterAffectedTree(children);
    const isNodeAffected =
      typeof node.status === "string" && AFFECTED_STATUSES.has(node.status);

    if (isNodeAffected || filteredChildren.length > 0) {
      acc.push({
        ...node,
        children: filteredChildren,
      } as AnyNodeTree);
    }
    return acc;
  }, []);
}

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
  const showAffectedOnly = useVersioningStore((s) => s.showAffectedOnly);
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
    const normalizedVersion = normalizeCommitId(data?.version);
    if (!checkedOutCommitId && normalizedVersion && headCommitId !== normalizedVersion) {
      setHeadCommitId(normalizedVersion);
    }
  }, [checkedOutCommitId, data?.version, headCommitId, setHeadCommitId]);

  useEffect(() => {
    if (data && isSuccess) {
      syncProjectData(data as ProjectNodeTree);
    }
  }, [data, isSuccess]); // eslint-disable-line react-hooks/exhaustive-deps

  const nodesForFiltering = useMemo(() => {
    const nodes = (rawProjectData?.children as AnyNodeTree[]) ?? [];
    if (!showAffectedOnly) return nodes;
    return filterAffectedTree(nodes);
  }, [rawProjectData?.children, showAffectedOnly]);

  // Tree Filtering
  const { filteredNodes, searchQuery, setSearchQuery } = useTreeFilter(
    nodesForFiltering
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

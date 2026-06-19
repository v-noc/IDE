import { useEffect, useEffectEvent, useMemo, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getApiErrorStatus } from "@/lib/api";

import { useGetProjectStructureTree } from "@/features/Dashboard/service/useProject";
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
  const navigate = useNavigate();

  const setProjectData = useProjectStore((s) => s.setProjectData);
  const rawProjectData = useProjectStore((s) => s.projectData);
  /** Which project root id we already auto-expanded (avoid refetch re-opening after user collapses). */
  const lastBootstrappedRootIdRef = useRef<string | null>(null);

  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const headCommitId = useVersioningStore((s) => s.headCommitId);
  const setHeadCommitId = useVersioningStore((s) => s.setHeadCommitId);
  const showAffectedOnly = useVersioningStore((s) => s.showAffectedOnly);
  const projectKey = projectId ? `ProjectSchema/${projectId}` : "";

  const { data, isLoading, isPending, isSuccess, isError, error } =
    useGetProjectStructureTree({
      key: projectKey,
    });

  useEffect(() => {
    if (!isError || getApiErrorStatus(error) !== 404) return;
    setProjectData(null);
    navigate("/", { replace: true });
  }, [isError, error, navigate, setProjectData]);

  /*
   * Sync server data to store.
   * Uses useEffectEvent to avoid reactive cycle with projectData.
   */
  const syncProjectData = useEffectEvent((newData: AnyNodeTree) => {
    const rootId = newData.id;
    const rootChanged = lastBootstrappedRootIdRef.current !== rootId;
    lastBootstrappedRootIdRef.current = rootId;

    setProjectData(newData as ProjectNodeTree);

    if (rootChanged) {
      const rootTabId = useTabStore.getState().rootTabId;
      useProjectStore.getState().expandNode(rootTabId, rootId);
    }
  });

  useEffect(() => {
    const normalizedVersion = normalizeCommitId(data?.version);
    if (!checkedOutCommitId && normalizedVersion && headCommitId !== normalizedVersion) {
      setHeadCommitId(normalizedVersion);
    }
  }, [checkedOutCommitId, data?.version, headCommitId, setHeadCommitId]);

  useEffect(() => {
    if (!projectKey) {
      lastBootstrappedRootIdRef.current = null;
    }
  }, [projectKey]);

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
    isStructurePending: isPending,
    projectKey,
    rawProjectData,
    filteredProjectData,
    searchQuery,
    setSearchQuery,
  };
}

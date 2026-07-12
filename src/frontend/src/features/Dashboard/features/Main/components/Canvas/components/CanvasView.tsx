import React, {
  useCallback,
  useMemo,
  useRef,
  useEffect,
  useEffectEvent,
} from "react";
import {
  Background,
  Controls,
  type FitViewOptions,
  type Node,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useTheme } from "next-themes";
import { useQueries, useQueryClient } from "@tanstack/react-query";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { SimpleTreeNode } from "./nodeUtils";
import EnhancedNode from "./nodes/EnhancedNode";
import { useEnhancedTreeLayout } from "../hooks/useEnhancedTreeLayout";
import { codeApi } from "@/services/code/api";
import {
  canLazyLoadCodeChildren,
  getCodeDescendantsQueryOptions,
} from "@/features/Dashboard/service/codeDescendants";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
import { findNodeByIdWithDescendantCache } from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import type { AnyNodeTree } from "@/types/project";
import { useShallow } from "zustand/react/shallow";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import {
  registerCanvas,
  unregisterCanvas,
} from "@/features/Dashboard/features/Agent/walkthrough/executor/canvasRegistry";
import { useWalkthroughStore } from "@/features/Dashboard/features/Agent/walkthrough/store/useWalkthroughStore";
import { cn } from "@/lib/utils";

const nodeTypes = {
  enhanced: EnhancedNode,
};

interface CanvasViewProps {
  tabId: string;
  projectId?: string;
}

const fitViewOptions: FitViewOptions = {
  padding: 0.2,
  minZoom: 0.4,
  maxZoom: 1.5,
};

const CanvasView: React.FC<CanvasViewProps> = ({
  tabId,
  projectId: _projectId,
}) => {
  void _projectId;

  const { resolvedTheme } = useTheme();
  const flowColorMode = resolvedTheme === "light" ? "light" : "dark";

  const queryClient = useQueryClient();

  const selectedNode = useProjectStore(
    useShallow((s) => s.selectedNode[tabId]),
  );
  const secondarySelectedNode = useProjectStore(
    useShallow((s) => s.secondarySelectedNode[tabId]),
  );
  const expandedNodeIds = useProjectStore(
    useShallow((s) => s.expandedNodeIds[tabId] ?? []),
  );
  const toggleNodeExpansion = useProjectStore(
    useShallow((s) => s.toggleNodeExpansion),
  );
  const expandNode = useProjectStore(useShallow((s) => s.expandNode));
  const expandNodesBulk = useProjectStore(useShallow((s) => s.expandNodesBulk));
  const projectData = useProjectStore(useShallow((s) => s.projectData));
  const handleNodeSelection = useTabStore(
    useShallow((s) => s.handleNodeSelection),
  );

  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const centerNode = selectedNode as SimpleTreeNode | null;
  const projectKey = projectData?.id ?? "";
  const isTourPlaying = useWalkthroughStore((s) => s.phase === "playing");
  const walkthroughForegroundNodeId = useWalkthroughStore((s) => {
    if (s.phase !== "playing") return null;
    return s.codeOpenNodeId ?? s.playerSteps[s.cursor]?.nodeId ?? null;
  });
  const reactFlowInstanceRef = useRef<ReactFlowInstance | null>(null);

  const layoutConfig = useMemo(
    () => ({
      LEVEL_SPACING_X: 450,
      SPACING_Y: 180,
      ROOT_X: -420,
      ROOT_Y: 0,
    }),
    [],
  );

  const effectiveSelectedNode = secondarySelectedNode
    ? secondarySelectedNode
    : centerNode;

  const lazyParentIds = useMemo(() => {
    if (!projectData || !projectKey) return [];
    const expandedSet = new Set(expandedNodeIds);
    const expansionBootstrapped = expandedNodeIds.length > 0;
    const layoutExpanded = (id: string) =>
      !expansionBootstrapped || expandedSet.has(id);

    const ids = new Set<string>();
    for (const id of expandedNodeIds) {
      // const n = findNodeByKey(projectData, id);
      ids.add(id);
    }
    const cid = effectiveSelectedNode?.id;

    if (cid && layoutExpanded(cid)) {
      // const n = findNodeByKey(projectData, cid);
      ids.add(cid);
    }
    return [...ids].sort();
  }, [projectData, projectKey, expandedNodeIds, effectiveSelectedNode?.id]);

  const descendantQueries = useQueries({
    queries: lazyParentIds.map((parentId) => ({
      ...getCodeDescendantsQueryOptions(
        projectKey,
        parentId,
        branch,
        ref,
        compareTo,
      ),
      enabled: Boolean(projectKey),
    })),
  });

  const descendantsDataKey = descendantQueries
    .map((query) => query.dataUpdatedAt)
    .join("|");

  const lazyChildrenByParentId = useMemo(() => {
    const m = new Map<string, AnyNodeTree[]>();
    lazyParentIds.forEach((parentId, i) => {
      const roots = descendantQueries[i]?.data?.children;
      if (roots?.length) {
        m.set(parentId, roots as unknown as AnyNodeTree[]);
      }
    });
    return m;
    // descendantsDataKey tracks descendant DATA changes; the query array identity
    // changes every render and must not be a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lazyParentIds, descendantsDataKey]);

  const { initialNodes, initialEdges } = useEnhancedTreeLayout({
    centerNode: centerNode,
    selectedNode: effectiveSelectedNode as SimpleTreeNode,
    expandedNodeIds,
    toggleNodeExpansion: (nodeId: string) => toggleNodeExpansion(tabId, nodeId),
    layoutConfig,
    lazyChildrenByParentId,
  });

  const nodesWithWalkthroughLayer = useMemo(() => {
    if (!isTourPlaying || !walkthroughForegroundNodeId) {
      return initialNodes;
    }
    const secondaryId = secondarySelectedNode?.id;
    return initialNodes.map((node) => {
      const isForeground = node.id === walkthroughForegroundNodeId;
      return {
        ...node,
        zIndex: isForeground ? 50 : 0,
        selected: isForeground || node.id === secondaryId,
      };
    });
  }, [
    initialNodes,
    isTourPlaying,
    walkthroughForegroundNodeId,
    secondarySelectedNode?.id,
  ]);

  const [nodes, setNodes, onNodesChange] = useNodesState(nodesWithWalkthroughLayer);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const centerTarget = useMemo(() => {
    const id = centerNode?.id;
    if (!id) return null;
    const n = nodes.find((node) => node.id === id);
    if (!n?.measured?.width) return null;
    return {
      id,
      x: n.position.x + n.measured.width / 2,
      y: n.position.y + (n.measured.height ?? 0) / 2,
    };
  }, [nodes, centerNode?.id]);

  const followSelectionRef = useRef(false);

  const syncDiffOverlay = useEffectEvent(() => {
    setNodes(nodesWithWalkthroughLayer);
    setEdges(initialEdges);
  });

  useEffect(() => {
    syncDiffOverlay();
  }, [nodesWithWalkthroughLayer, initialEdges]);

  useEffect(() => {
    if (!centerNode?.id) return;
    const nodeId = centerNode.id;
    const pk = projectData?.id ?? "";
    if (!pk) {
      expandNode(tabId, nodeId);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const { path_ids } = await codeApi.getLineage(pk, nodeId);
        if (cancelled) return;
        if (path_ids?.length) {
          expandNodesBulk(tabId, path_ids);
          return;
        }
      } catch {
        /* fall through */
      }
      if (!cancelled) expandNode(tabId, nodeId);
    })();
    return () => {
      cancelled = true;
    };
  }, [centerNode?.id, projectData?.id, tabId, expandNodesBulk, expandNode]);

  useEffect(() => {
    followSelectionRef.current = true;
  }, [centerNode?.id]);

  useEffect(() => {
    if (!centerTarget || !followSelectionRef.current) return;
    if (useWalkthroughStore.getState().phase === "playing") return;
    reactFlowInstanceRef.current?.setCenter(centerTarget.x, centerTarget.y, {
      zoom: 1,
      duration: 300,
    });
  }, [centerTarget]);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstanceRef.current = instance;
    registerCanvas(tabId, instance);
  }, [tabId]);

  useEffect(() => {
    return () => unregisterCanvas(tabId);
  }, [tabId]);

  const onMoveStart = useCallback((event?: MouseEvent | TouchEvent | null) => {
    if (!event) return;
    followSelectionRef.current = false;
    if (useWalkthroughStore.getState().phase === "playing") {
      useWalkthroughStore.getState().setUserInteracted(true);
    }
  }, []);

  const onMove = useCallback(() => {
    if (useWalkthroughStore.getState().phase === "playing") {
      useWalkthroughStore.getState().bumpAnchorEpoch();
    }
  }, []);

  const onNodeDrag = useCallback(() => {
    if (useWalkthroughStore.getState().phase === "playing") {
      useWalkthroughStore.getState().bumpAnchorEpoch();
    }
  }, []);

  const onNodeDoubleClick = useCallback((_: React.MouseEvent, node: Node) => {
    if (!reactFlowInstanceRef.current) return;
    reactFlowInstanceRef.current.setCenter(
      node.position.x + (node.measured?.width || 0) / 2,
      node.position.y + (node.measured?.height || 0) / 2,
      {
        zoom: 1,
        duration: 300,
      },
    );
  }, []);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (useWalkthroughStore.getState().phase === "playing") {
        return;
      }
      const nodeKey = node.id;
      if (!nodeKey) return;
      const foundNode = findNodeByIdWithDescendantCache(
        queryClient,
        projectData,
        projectKey,
        nodeKey,
      );
      if (!foundNode) return;
      if (foundNode.id !== centerNode?.id) {
        handleNodeSelection(tabId, foundNode, "secondary");
      } else {
        handleNodeSelection(tabId, foundNode, "primary");
      }
    },
    [
      queryClient,
      projectData,
      projectKey,
      handleNodeSelection,
      tabId,
      centerNode?.id,
    ],
  );

  return (
    <div
      className={cn(
        "h-full w-full bg-background",
        isTourPlaying && "walkthrough-playing",
      )}
    >
      <ReactFlow
        colorMode={flowColorMode}
        className="bg-background"
        nodeTypes={nodeTypes}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onInit={onInit}
        onMoveStart={onMoveStart}
        onMove={onMove}
        onNodeDrag={onNodeDrag}
        onNodeDoubleClick={onNodeDoubleClick}
        onNodeClick={onNodeClick}
        nodesDraggable={true}
        minZoom={0.01}
        nodesConnectable={false}
        elementsSelectable={true}
        fitView
        fitViewOptions={fitViewOptions}
        panOnDrag={true}
        selectionOnDrag={false}
        multiSelectionKeyCode={null}
        deleteKeyCode={null}
      >
        <Background />
        <Controls position="bottom-right" />
      </ReactFlow>
    </div>
  );
};

export default CanvasView;

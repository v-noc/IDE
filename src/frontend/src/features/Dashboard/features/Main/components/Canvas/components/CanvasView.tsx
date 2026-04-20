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

  const lazyChildrenByParentId = useMemo(() => {
    const m = new Map<string, AnyNodeTree[]>();
    lazyParentIds.forEach((parentId, i) => {
      const roots = descendantQueries[i]?.data?.children;
      if (roots?.length) {
        m.set(parentId, roots as unknown as AnyNodeTree[]);
      }
    });
    return m;
  }, [lazyParentIds, descendantQueries]);

  const { initialNodes, initialEdges } = useEnhancedTreeLayout({
    centerNode: centerNode,
    selectedNode: effectiveSelectedNode as SimpleTreeNode,
    expandedNodeIds,
    toggleNodeExpansion: (nodeId: string) => toggleNodeExpansion(tabId, nodeId),
    layoutConfig,
    lazyChildrenByParentId,
  });

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const syncDiffOverlay = useEffectEvent(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  });

  useEffect(() => {
    syncDiffOverlay();
  }, [initialNodes, initialEdges]);

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

  const lastCenteredTargetIdRef = useRef<string | null>(null);

  const centerOnTarget = useEffectEvent(() => {
    const nodeId = centerNode?.id;
    if (!nodeId || nodes.length === 0 || !reactFlowInstanceRef.current) {
      return;
    }

    const rfNode = nodes.find((n) => n.id === nodeId);

    // Check if node exists and has been measured (width > 0)
    if (rfNode && rfNode.measured?.width) {
      if (lastCenteredTargetIdRef.current !== nodeId) {
        reactFlowInstanceRef.current.setCenter(
          rfNode.position.x + (rfNode.measured?.width ?? 0) / 2,
          rfNode.position.y + (rfNode.measured?.height ?? 0) / 2,
          {
            zoom: 1,
            duration: 300,
          },
        );
        lastCenteredTargetIdRef.current = nodeId;
      }
    } else {
      // If node not found yet or dimensions not measured, retry next frame.
      requestAnimationFrame(centerOnTarget);
    }
  });

  useEffect(() => {
    if (centerNode) {
      centerOnTarget();
    } else {
      lastCenteredTargetIdRef.current = null;
    }
  }, [centerNode, centerOnTarget]);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstanceRef.current = instance;
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
    <div className="h-full w-full bg-background">
      <ReactFlow
        colorMode={flowColorMode}
        className="bg-background"
        nodeTypes={nodeTypes}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onInit={onInit}
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

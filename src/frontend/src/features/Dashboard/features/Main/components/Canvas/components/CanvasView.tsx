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
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { SimpleTreeNode } from "./nodeUtils";
import EnhancedNode from "./nodes/EnhancedNode";
import { useEnhancedTreeLayout } from "../hooks/useEnhancedTreeLayout";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
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

  const selectedNode = useProjectStore(
    useShallow((s) => s.selectedNode[tabId])
  );
  const expandedNodeIds = useProjectStore(
    useShallow((s) => s.expandedNodeIds[tabId] ?? [])
  );
  const toggleNodeExpansion = useProjectStore(
    useShallow((s) => s.toggleNodeExpansion)
  );
  const projectData = useProjectStore(useShallow((s) => s.projectData));
  const handleNodeSelection = useTabStore(
    useShallow((s) => s.handleNodeSelection)
  );

  const centerNode = selectedNode as SimpleTreeNode | null;
  const reactFlowInstanceRef = useRef<ReactFlowInstance | null>(null);

  const layoutConfig = useMemo(
    () => ({
      LEVEL_SPACING_X: 450,
      SPACING_Y: 180,
      ROOT_X: -420,
      ROOT_Y: 0,
    }),
    []
  );

  const focusTargetId = useProjectStore(
    useShallow((s) => s.focusTargetId[tabId])
  );

  const { initialNodes, initialEdges } = useEnhancedTreeLayout({
    centerNode,
    expandedNodeIds,
    toggleNodeExpansion: (nodeId: string) => toggleNodeExpansion(tabId, nodeId),
    layoutConfig,
    focusTargetId,
  });

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const lastCenteredTargetIdRef = useRef<string | null>(null);

  const centerOnTarget = useEffectEvent(() => {
    if (!focusTargetId || nodes.length === 0 || !reactFlowInstanceRef.current) {
      return;
    }

    // Robustly extract the key from the ID
    const cleanId = focusTargetId.includes("/")
      ? focusTargetId.split("/").pop()!
      : focusTargetId;

    const rfNode = nodes.find((n) => n.id === cleanId);

    // Check if node exists and has been measured (width > 0)
    if (rfNode && rfNode.measured?.width) {
      if (lastCenteredTargetIdRef.current !== focusTargetId) {
        reactFlowInstanceRef.current.setCenter(
          rfNode.position.x + (rfNode.measured?.width ?? 0) / 2,
          rfNode.position.y + (rfNode.measured?.height ?? 0) / 2,
          {
            zoom: 1,
            duration: 300,
          }
        );
        lastCenteredTargetIdRef.current = focusTargetId;
      }
    } else {
      // If node not found yet or dimensions not measured, retry next frame.
      requestAnimationFrame(centerOnTarget);
    }
  });

  useEffect(() => {
    if (focusTargetId) {
      centerOnTarget();
    } else {
      lastCenteredTargetIdRef.current = null;
    }
  }, [focusTargetId]);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstanceRef.current = instance;
  }, []);

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const nodeKey = node.id;
      if (projectData && nodeKey && reactFlowInstanceRef.current) {
        const foundNode = findNodeByKey(projectData, nodeKey);
        if (foundNode) {
          reactFlowInstanceRef.current.setCenter(
            node.position.x + (node.measured?.width || 0) / 2,
            node.position.y + (node.measured?.height || 0) / 2,
            {
              zoom: 1,
              duration: 300,
            }
          );
        }
      }
    },
    [projectData]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const nodeKey = node.id;
      if (projectData && nodeKey) {
        const foundNode = findNodeByKey(projectData, nodeKey);
        if (foundNode?._key) {
          handleNodeSelection(tabId, foundNode, "secondary");
        }
      }
    },
    [projectData, handleNodeSelection, tabId]
  );

  return (
    <div className="h-full w-full bg-slate-50">
      <ReactFlow
        className="bg-transparent"
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

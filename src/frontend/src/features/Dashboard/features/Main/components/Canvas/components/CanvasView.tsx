import React, { useCallback, useMemo, useRef, useEffect, useEffectEvent } from "react";
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

const nodeTypes = {
  enhanced: EnhancedNode,
};

interface CanvasViewProps {
  projectId?: string;
}

const fitViewOptions: FitViewOptions = {
  padding: 0.2,
  minZoom: 0.4,
  maxZoom: 1.5,
};

const CanvasView: React.FC<CanvasViewProps> = ({ projectId: _projectId }) => {
  void _projectId;
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  const projectData = useProjectStore((s) => s.projectData);

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

  const focusTargetId = useProjectStore((s) => s.focusTargetId);

  const { initialNodes, initialEdges } = useEnhancedTreeLayout({
    centerNode,
    expandedNodeIds,
    toggleNodeExpansion,
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
          rfNode.position.x + rfNode.measured.width / 2,
          rfNode.position.y + rfNode.measured.height / 2,
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

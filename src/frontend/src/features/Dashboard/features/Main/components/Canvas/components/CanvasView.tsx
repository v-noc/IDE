import React, { useCallback, useMemo, useRef } from "react";
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
import EnhancedNode from "./EnhancedNode";
import { useEnhancedTreeLayout } from "../hooks/useEnhancedTreeLayout";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";

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
  const {
    selectedNode,
    expandedNodeIds,
    toggleNodeExpansion,
    setSelectedNode,
    projectData,
  } = useProjectStore();

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

  const { initialNodes, initialEdges } = useEnhancedTreeLayout({
    centerNode,
    expandedNodeIds,
    toggleNodeExpansion,
    layoutConfig,
  });

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  React.useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const nodeTypes = useMemo(() => ({ enhanced: EnhancedNode }), []);

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstanceRef.current = instance;
  }, []);

  const onNodeDoubleClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      // Find the actual node tree data by key
      const nodeKey = node.id;
      if (projectData && nodeKey && reactFlowInstanceRef.current) {
        const foundNode = findNodeByKey(projectData, nodeKey);
        if (foundNode) {
          // Set as selected node
          // setSelectedNode(foundNode);

          // Center the view on this node
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

import React from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  BackgroundVariant,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useCanvasGraph } from "../hooks/useCanvasGraph";
import { nodeTypes } from "../wiring/nodeTypes";
import { edgeTypes } from "../wiring/edgeTypes";

import useProjectStore from "@/features/Dashboard/store/useProjectStore";

interface CanvasViewProps {
  projectId?: string;
}

const CanvasView: React.FC<CanvasViewProps> = ({ projectId }) => {
  const { setSelectedNodeId, toggleNodeExpansion } = useProjectStore();

  const { initialNodes, initialEdges, onConnect } = useCanvasGraph(projectId);

  const [nodes, , handleNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, handleEdgesChange] = useEdgesState(initialEdges);

  const handleConnect = onConnect(setEdges);

  const onNodeClick: NodeMouseHandler = (_event, node) => {
    setSelectedNodeId(node.id);
  };

  const onNodeDoubleClick: NodeMouseHandler = (_event, node) => {
    toggleNodeExpansion(node.id);
  };

  return (
    <div className="h-[calc(100vh-140px)] w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={(changes) => handleNodesChange(changes)}
        onEdgesChange={(changes) => handleEdgesChange(changes)}
        onConnect={handleConnect}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <MiniMap pannable zoomable />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
};

export default CanvasView;

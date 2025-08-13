import React, { useEffect } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useCanvasGraph } from "../hooks/useCanvasGraph";
import { nodeTypes } from "../wiring/nodeTypes";
import { edgeTypes } from "../wiring/edgeTypes";

interface CanvasViewProps {
  projectId?: string;
}

const CanvasView: React.FC<CanvasViewProps> = ({ projectId }) => {
  const { initialNodes, initialEdges, onConnect, doNotReRenderCanvas } =
    useCanvasGraph(projectId);

  const [nodes, setNodes, handleNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, handleEdgesChange] = useEdgesState(initialEdges);

  const handleConnect = onConnect(setEdges);

  // keep local state in sync with derived graph
  useEffect(() => {
    if (!doNotReRenderCanvas) {
      setNodes([...initialNodes]);
    }
  }, [initialNodes, setNodes]);

  useEffect(() => {
    if (!doNotReRenderCanvas) {
      setEdges([...initialEdges]);
    }
  }, [initialEdges, setEdges]);

  return (
    <div className="h-[calc(100vh-140px)] w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={(changes) => handleNodesChange(changes)}
        onEdgesChange={(changes) => handleEdgesChange(changes)}
        onConnect={handleConnect}
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

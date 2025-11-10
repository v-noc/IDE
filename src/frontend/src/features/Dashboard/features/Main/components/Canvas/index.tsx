import React from "react";
import { ReactFlowProvider } from "@xyflow/react";
import CanvasView from "./view/CanvasView";
// import useProjectStore from "@/features/Dashboard/store/useProjectStore";,

interface CanvasProps {
  projectId?: string;
}

const Canvas: React.FC<CanvasProps> = ({ projectId }) => {
  // const { selectedNode, projectData, focusedNode } = useProjectStore();
  return (
    <ReactFlowProvider>
      <CanvasView projectId={projectId} />
    </ReactFlowProvider>
  );
};

export default Canvas;

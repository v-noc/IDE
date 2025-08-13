import React from "react";
import { ReactFlowProvider } from "@xyflow/react";
import CanvasView from "./view/CanvasView";

interface CanvasProps {
  projectId?: string;
}

const Canvas: React.FC<CanvasProps> = ({ projectId }) => {
  return (
    <ReactFlowProvider>
      <CanvasView projectId={projectId} />
    </ReactFlowProvider>
  );
};

export default Canvas;

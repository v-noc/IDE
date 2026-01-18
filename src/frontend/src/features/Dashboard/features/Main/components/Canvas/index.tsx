import React from "react";
import { ReactFlowProvider } from "@xyflow/react";
import CanvasView from "./components/CanvasView";
// import useProjectStore from "@/features/Dashboard/store/useProjectStore";,

interface CanvasProps {
  tabId: string;
  projectId?: string;
}

const Canvas: React.FC<CanvasProps> = ({ tabId, projectId }) => {
  // const { selectedNode, projectData, focusedNode } = useProjectStore();

  return (
    <ReactFlowProvider>
      <CanvasView tabId={tabId} projectId={projectId} />
    </ReactFlowProvider>
  );
};

export default Canvas;

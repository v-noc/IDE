import React from "react";
import { ReactFlowProvider } from "@xyflow/react";
import CanvasView from "./components/CanvasView";
import { WalkthroughProvider } from "@/features/Dashboard/features/Agent/walkthrough/components/WalkthroughProvider";

interface CanvasProps {
  tabId: string;
  projectId?: string;
}

const Canvas: React.FC<CanvasProps> = ({ tabId, projectId }) => {
  return (
    <ReactFlowProvider>
      <CanvasView tabId={tabId} projectId={projectId} />
      <WalkthroughProvider tabId={tabId} />
    </ReactFlowProvider>
  );
};

export default Canvas;

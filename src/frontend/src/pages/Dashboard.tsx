import { useParams } from "react-router-dom";
import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import Workspace from "@/features/Dashboard/features/Main";
import { ResizablePanelGroup } from "@/components/ui/resizable";
import { RightSidebar } from "@/features/Dashboard/features/Main/components/RightSidebar";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useEffect } from "react";
import { useGroupFlattening } from "@/features/Dashboard/hooks/useGroupFlattening";
import { useSocketSync, useProjectRoom } from "@/services/socket";

/**
 * Dashboard Page - Entry point for the IDE dashboard.
 * Orchestrates the high-level layout and global sub-systems.
 */
const Dashboard = () => {
  const { projectId } = useParams();
  const { selectedNode, projectData, setSelectedNode } = useProjectStore();

  // Socket and Data Sync hooks
  useSocketSync();
  useProjectRoom(projectId);

  // Transformation hooks
  useGroupFlattening();

  // Set default selection to project root if nothing is selected
  useEffect(() => {
    if (selectedNode == null && projectData != null) {
      setSelectedNode(projectData);
    }
  }, [selectedNode, projectData, setSelectedNode]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <RightSidebar>
            <Workspace />
          </RightSidebar>
        }
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;

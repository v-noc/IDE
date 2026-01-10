import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/componets/Navbar";
import MainCanvas from "@/features/Dashboard/features/Main";
import { ResizablePanelGroup } from "@/components/ui/resizable";
import MainWithRightSidebar from "@/features/Dashboard/features/Main/MainWithRightSidebar";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useEffect } from "react";
import { useGroupFlattening } from "@/features/Dashboard/hooks/useGroupFlattening";
import { useSocketConnection } from "@/services/socket";

/**
 * Dashboard Page - Entry point for the IDE dashboard.
 * Orchestrates the high-level layout and global side effects.
 */
const Dashboard = () => {
  const { selectedNode, projectData, setSelectedNode } = useProjectStore();

  // Data processing hooks
  useGroupFlattening();
  useSocketConnection();

  // Set default selection to project root if nothing is selected
  useEffect(() => {
    if (selectedNode == null && projectData != null) {
      setSelectedNode(projectData);
    }
  }, [selectedNode, projectData, setSelectedNode]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={<MainWithRightSidebar left={<MainCanvas />} />}
        navbar={<Navbar />}
        leftSidebar={<SideBar />}
      />
    </ResizablePanelGroup>
  );
};

export default Dashboard;

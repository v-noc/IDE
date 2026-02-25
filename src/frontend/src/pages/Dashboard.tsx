import { useParams } from "react-router-dom";
import Layout from "@/features/Dashboard/components/Layout";
import SideBar from "@/features/Dashboard/features/Sidebar/components/SideBar";
import Navbar from "@/features/Dashboard/features/Navbar/components/Navbar";
import Workspace from "@/features/Dashboard/features/Main";
import { ResizablePanelGroup } from "@/components/ui/resizable";
import { RightSidebar } from "@/features/Dashboard/features/Main/components/RightSidebar";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { useEffect } from "react";
import { useGroupFlattening } from "@/features/Dashboard/hooks/useGroupFlattening";
import { useSocketSync, useProjectRoom } from "@/services/socket";

import { selectTabStack } from "@/features/Dashboard/store/selectors/tabSelectors";
import { cn } from "@/lib/utils";

import { useShallow } from "zustand/react/shallow";
import { SidebarDialogs } from "@/features/Dashboard/components/SidebarDialogs";
import VersioningPanel from "@/features/Dashboard/features/Versioning/components/VersioningPanel";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

/**
 * Dashboard Page - Entry point for the IDE dashboard.
 * Orchestrates the high-level layout and global sub-systems.
 */
const Dashboard = () => {
  const { projectId } = useParams();
  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);
  const projectData = useProjectStore((s) => s.projectData);
  const handleNodeSelection = useTabStore((s) => s.handleNodeSelection);

  const tabStack = useTabStore(useShallow(selectTabStack));
  const isVersioningOpen = useVersioningStore((s) => s.isOpen);

  // Socket and Data Sync hooks
  useSocketSync();
  useProjectRoom(projectId);

  // Transformation hooks
  useGroupFlattening();

  // Set default selection for the active tab if nothing is selected
  useEffect(() => {
    if (!selectedNode && projectData != null) {
      handleNodeSelection(activeTabId, projectData, "primary");
    }
  }, [selectedNode, projectData, handleNodeSelection, activeTabId]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <RightSidebar>
            {tabStack.map((tab) => (
              <div
                key={tab.id}
                className={cn(
                  "h-full w-full",
                  tab.id !== activeTabId && "hidden",
                )}
              >
                <Workspace tabId={tab.id} />
              </div>
            ))}
          </RightSidebar>
        }
        navbar={<Navbar projectId={projectId} />}
        leftSidebar={<SideBar />}
        rightSidebar={
          isVersioningOpen ? <VersioningPanel tabId={activeTabId} /> : undefined
        }
      />
      <SidebarDialogs />
    </ResizablePanelGroup>
  );
};

export default Dashboard;

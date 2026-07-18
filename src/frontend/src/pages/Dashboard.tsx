import { useParams, useSearchParams } from "react-router-dom";
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
import { TaskDetailPanel } from "@/features/Dashboard/features/Tasks/components/detail/TaskDetailPanel";
import { findNodeByIdWithDescendantCache } from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import { useQueryClient } from "@tanstack/react-query";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import AgentOverlay from "@/features/Dashboard/features/Agent";
import VersioningStatusBanner from "@/features/Dashboard/features/Versioning/components/VersioningStatusBanner";
import { useDashboardDeepLinkFocus } from "@/features/Dashboard/hooks/useDashboardDeepLinkFocus";

/**
 * Dashboard Page - Entry point for the IDE dashboard.
 * Orchestrates the high-level layout and global sub-systems.
 */
const Dashboard = () => {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const focusLinkPending = Boolean(
    searchParams.get("focus")?.length || searchParams.get("share")?.length,
  );
  const activeTabId = useTabStore((s) => s.activeTabId);
  const selectedNode = useProjectStore((s) => s.selectedNode[activeTabId]);
  const projectData = useProjectStore((s) => s.projectData);
  const handleNodeSelection = useTabStore((s) => s.handleNodeSelection);

  const tabStack = useTabStore(useShallow(selectTabStack));
  const isVersioningOpen = useVersioningStore((s) => s.isOpen);
  const selectedTaskId = useProjectStore((s) => s.selectedTaskId);
  const queryClient = useQueryClient();
  const pushFocus = useProjectStore((s) => s.pushFocus);

  const handleTaskNavigateToNode = (nodeId: string) => {
    const projectKey = projectData?.id ?? "";
    const node = findNodeByIdWithDescendantCache(
      queryClient,
      projectData,
      projectKey,
      nodeId,
    );
    if (node) {
      pushFocus(activeTabId, node);
    }
  };

  // Socket and Data Sync hooks
  useSocketSync();
  useProjectRoom(projectId);

  // Transformation hooks
  useGroupFlattening();

  useDashboardDeepLinkFocus(projectId);

  // Set default selection for the active tab if nothing is selected
  useEffect(() => {
    if (!selectedNode && projectData != null && !focusLinkPending) {
      handleNodeSelection(activeTabId, projectData, "primary");
    }
  }, [
    selectedNode,
    projectData,
    handleNodeSelection,
    activeTabId,
    focusLinkPending,
  ]);

  return (
    <ResizablePanelGroup direction="horizontal">
      <Layout
        main={
          <div className="flex h-full min-h-0 w-full flex-col">
            <VersioningStatusBanner />
            <div className="min-h-0 flex-1">
              <RightSidebar>
                {tabStack.map((tab) => (
                  <div
                    key={tab.id}
                    className={cn(
                      "relative h-full w-full",
                      tab.id !== activeTabId && "hidden",
                    )}
                  >
                    <Workspace tabId={tab.id} />
                    <AgentOverlay />
                  </div>
                ))}
              </RightSidebar>
            </div>
          </div>
        }
        navbar={<Navbar projectId={projectId} />}
        leftSidebar={<SideBar />}
        rightSidebar={
          selectedTaskId ? (
            <TaskDetailPanel
              projectId={projectId ?? ""}
              tabId={activeTabId}
              onNavigateToNode={handleTaskNavigateToNode}
            />
          ) : isVersioningOpen ? (
            <VersioningPanel tabId={activeTabId} />
          ) : undefined
        }
      />
      <SidebarDialogs />
    </ResizablePanelGroup>
  );
};

export default Dashboard;

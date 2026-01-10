
import {
  ResizableHandle,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Panel as ResizablePanel } from "react-resizable-panels";
import { FolderTree } from "lucide-react";
import ProjectTree from "./ProjectTree";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarDialogs } from "./SidebarDialogs";
import { Skeleton } from "@/components/ui/skeleton";
import { useSidebarData } from "../hooks/useSidebarData";
import { useSidebarPanels } from "../hooks/useSidebarPanels";

/**
 * Main SideBar component (Orchestrator).
 * Uses modular hooks for data and layout management.
 */
const SideBar = () => {
  const {
    isLoading,
    filteredProjectData,
    searchQuery,
    setSearchQuery,
  } = useSidebarData();

  const {
    projectFilePanelRef,
    onCollapse,
    onExpand,
  } = useSidebarPanels();

  return (
    <div className="h-full w-full flex flex-col gap-2 bg-sidebar transition-colors duration-300">
      <SidebarHeader
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />

      <ResizablePanelGroup direction="vertical" className="flex-1">
        <ResizablePanel
          ref={projectFilePanelRef}
          minSize={20}
          onCollapse={onCollapse}
          onExpand={onExpand}
          className="flex flex-col"
        >
          <div className="h-full flex flex-col pt-2">
            <div className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground/70 px-4 flex items-center gap-2 py-2 select-none">
              <FolderTree size={14} className="text-primary/70" />
              <span>Project Tree</span>
            </div>

            <div className="flex-1 overflow-y-auto px-2 pb-4">
              {isLoading ? (
                <div className="space-y-2 p-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-4 w-5/6" />
                </div>
              ) : (
                filteredProjectData && (
                  <ProjectTree projectTree={filteredProjectData} />
                )
              )}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle
          withHandle
          className="opacity-0 hover:opacity-100 transition-opacity"
        />

        {/* Fill the remaining space */}
        <ResizablePanel defaultSize={0} minSize={0} />
      </ResizablePanelGroup>

      <SidebarDialogs />
    </div>
  );
};

export default SideBar;

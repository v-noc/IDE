import { Link, useParams } from "react-router-dom";
import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import ProjectTree from "./ProjectTree";
import VirtualFolders from "./VirtualFolders/VirtualFolders";
import {
  ResizableHandle,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Panel as ResizablePanel,
  type ImperativePanelHandle,
} from "react-resizable-panels";
import { ChevronDownIcon } from "lucide-react";
import { PiShareNetworkFill } from "react-icons/pi";
import { useState, useRef, useEffect } from "react";
import CreateVirtualFolderDialog from "./VirtualFolders/CreateVirtualFolderDialog";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { Skeleton } from "@/components/ui/skeleton";
import { useQueryClient } from "@tanstack/react-query";
import { Separator } from "@/components/ui/separator";

const SideBar = () => {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const { data, isLoading, isSuccess, dataUpdatedAt } =
    useGetProjectTreeWithKeyProject({
      key: projectId || "",
    });

  const { setProjectData, projectData } = useProjectStore();

  // Update project data in store when data changes
  useEffect(() => {
    if (data && isSuccess) {
      setProjectData(data);
    }
  }, [data, setProjectData, isSuccess, dataUpdatedAt]);

  // Listen for code saves to resync tree without resetting UI state
  useEffect(() => {
    const handler = () => {
      if (!projectId) return;
      queryClient.invalidateQueries({ queryKey: ["projectTree", projectId] });
    };
    window.addEventListener("code-saved", handler);
    return () => window.removeEventListener("code-saved", handler);
  }, [projectId, queryClient]);

  const [isProjectFilesCollapsed, setProjectFilesCollapsed] = useState(false);
  const [isVirtualFoldersCollapsed, setVirtualFoldersCollapsed] =
    useState(false);

  const projectFilePanelRef = useRef<ImperativePanelHandle>(null);
  const virtualFoldersPanelRef = useRef<ImperativePanelHandle>(null);

  const toggleProjectFiles = () => {
    const panel = projectFilePanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        if (isVirtualFoldersCollapsed) {
          virtualFoldersPanelRef.current?.expand();
        }
        panel.collapse();
      }
    }
  };

  const toggleVirtualFolders = () => {
    const panel = virtualFoldersPanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        if (isProjectFilesCollapsed) {
          projectFilePanelRef.current?.expand();
        }
        panel.collapse();
      }
    }
  };

  return (
    <div className=" h-full w-full flex flex-col gap-2">
      <Link to="/">
        <div className="text-2xl font-bold flex items-center p-4 gap-2 h-[57px]  text-white">
          <PiShareNetworkFill className="size-6  fill-green-600" />
          <span className=" text-black  ">V-NOC</span>
        </div>
      </Link>
      <Separator />
      <ResizablePanelGroup direction="vertical" className="p-2">
        <ResizablePanel
          ref={projectFilePanelRef}
          collapsible
          collapsedSize={4}
          minSize={10}
          onCollapse={() => {
            if (isVirtualFoldersCollapsed) {
              virtualFoldersPanelRef.current?.expand();
            }
            setProjectFilesCollapsed(true);
          }}
          onExpand={() => setProjectFilesCollapsed(false)}
        >
          <div className="h-full flex flex-col">
            <div
              className="text-xs font-medium text-gray-600 px-2 flex items-center gap-4 hover:no-underline py-1 cursor-pointer"
              onClick={toggleProjectFiles}
            >
              <ChevronDownIcon
                className={`text-muted-foreground transition-transform duration-200 ${
                  !isProjectFilesCollapsed && "rotate-180"
                }`}
                size={16}
              />
              <span>Project Node</span>
            </div>
            <Separator />
            {!isProjectFilesCollapsed && (
              <div className="py-2 flex-grow overflow-y-auto">
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : (
                  projectData && <ProjectTree projectTree={projectData} />
                )}
              </div>
            )}
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel
          ref={virtualFoldersPanelRef}
          collapsible
          collapsedSize={4}
          className={isVirtualFoldersCollapsed ? "pb-4" : ""}
          minSize={10}
          onCollapse={() => {
            if (isProjectFilesCollapsed) {
              projectFilePanelRef.current?.expand();
            }
            setVirtualFoldersCollapsed(true);
          }}
          onExpand={() => setVirtualFoldersCollapsed(false)}
        >
          <div className={`h-full flex flex-col`}>
            <div className="text-xs font-medium text-gray-600 px-2 flex items-center justify-between hover:no-underline py-1">
              <div
                className="flex items-center gap-4 cursor-pointer flex-1"
                onClick={toggleVirtualFolders}
              >
                <ChevronDownIcon
                  className={`text-muted-foreground transition-transform duration-200 ${
                    !isVirtualFoldersCollapsed && "rotate-180"
                  }`}
                  size={16}
                />
                <span>Nodes Branch</span>
              </div>
              <CreateVirtualFolderDialog />
            </div>
            {!isVirtualFoldersCollapsed && (
              <div className="flex-grow overflow-y-auto h-full">
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : (
                  <VirtualFolders />
                )}
              </div>
            )}
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

export default SideBar;

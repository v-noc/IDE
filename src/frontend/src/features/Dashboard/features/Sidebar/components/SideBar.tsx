import { Link, useParams } from "react-router-dom";
import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import ProjectTree from "./ProjectTree";
import CustomFolders from "./CustomFolders/CustomFolders";
import {
  ResizableHandle,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Panel as ResizablePanel,
  type ImperativePanelHandle,
} from "react-resizable-panels";
import { ChevronDownIcon } from "lucide-react";
import { useState, useRef } from "react";
import CreateVirtualFolderDialog from "./CustomFolders/CreateVirtualFolderDialog";

const SideBar = () => {
  const { projectId } = useParams();
  const { data } = useGetProjectTreeWithKeyProject({
    key: projectId || "",
  });

  const [isProjectFilesCollapsed, setProjectFilesCollapsed] = useState(false);
  const [isCustomFoldersCollapsed, setCustomFoldersCollapsed] = useState(false);

  const projectFilePanelRef = useRef<ImperativePanelHandle>(null);
  const customFoldersPanelRef = useRef<ImperativePanelHandle>(null);

  const toggleProjectFiles = () => {
    const panel = projectFilePanelRef.current;
    if (panel) {
      if (panel.isCollapsed()) {
        panel.expand();
      } else {
        if (isCustomFoldersCollapsed) {
          customFoldersPanelRef.current?.expand();
        }
        panel.collapse();
      }
    }
  };

  const toggleCustomFolders = () => {
    const panel = customFoldersPanelRef.current;
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
        <div className="text-2xl font-bold flex items-center  h-[57px] bg-sky-600 text-white">
          <span className="pl-4 text-white  ">v-noc</span>
        </div>
      </Link>
      <ResizablePanelGroup direction="vertical" className="p-2">
        <ResizablePanel
          ref={projectFilePanelRef}
          collapsible
          collapsedSize={4}
          minSize={10}
          onCollapse={() => {
            if (isCustomFoldersCollapsed) {
              customFoldersPanelRef.current?.expand();
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
              <span>Project Files</span>
            </div>
            {!isProjectFilesCollapsed && (
              <div className="py-2 flex-grow overflow-y-auto">
                {data && <ProjectTree projectTree={data} />}
              </div>
            )}
          </div>
        </ResizablePanel>
        <ResizableHandle
          withHandle
          disabled={isProjectFilesCollapsed || isCustomFoldersCollapsed}
        />
        <ResizablePanel
          ref={customFoldersPanelRef}
          collapsible
          collapsedSize={4}
          className={isCustomFoldersCollapsed ? "pb-4" : ""}
          minSize={10}
          onCollapse={() => {
            if (isProjectFilesCollapsed) {
              projectFilePanelRef.current?.expand();
            }
            setCustomFoldersCollapsed(true);
          }}
          onExpand={() => setCustomFoldersCollapsed(false)}
        >
          <div className={`h-full flex flex-col`}>
            <div className="text-xs font-medium text-gray-600 px-2 flex items-center justify-between hover:no-underline py-1">
              <div
                className="flex items-center gap-4 cursor-pointer flex-1"
                onClick={toggleCustomFolders}
              >
                <ChevronDownIcon
                  className={`text-muted-foreground transition-transform duration-200 ${
                    !isCustomFoldersCollapsed && "rotate-180"
                  }`}
                  size={16}
                />
                <span>Custom Folders</span>
              </div>
              <CreateVirtualFolderDialog />
            </div>
            {!isCustomFoldersCollapsed && (
              <div className="flex-grow overflow-y-auto h-full">
                <CustomFolders />
              </div>
            )}
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

export default SideBar;

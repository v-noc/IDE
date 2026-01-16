import { memo, Fragment } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ContextPanel } from "./ContextPanel";
import { selectTabStack } from "../../../store/selectors/tabSelectors";
import useProjectStore from "../../../store/useProjectStore";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarDialogs } from "./SidebarDialogs";

import { useSidebarData } from "../hooks/useSidebarData";

import { useShallow } from "zustand/react/shallow";

/**
 * Main Sidebar Container
 * Manages the layout of project tree, search, and other sidebar features.
 * Supports hierarchical Context Panels.
 */
export const SideBar = memo(function SideBar() {
  const activeTabId = useProjectStore((s) => s.activeTabId);
  const setActiveTabId = useProjectStore((s) => s.setActiveTabId);
  const destroyTabBranch = useProjectStore((s) => s.destroyTabBranch);
  const projectData = useProjectStore((s) => s.projectData);

  const tabStack = useProjectStore(useShallow(selectTabStack));

  const { filteredProjectData, searchQuery, setSearchQuery } = useSidebarData();

  if (!projectData) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
        No project loaded
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-sidebar border-r overflow-hidden">
      {/* 1. Static Header */}
      <div className="flex-none transition-all duration-300">
        <SidebarHeader
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />
      </div>

      {/* 2. Dynamic Context Stack */}
      <div className="flex-1 overflow-hidden">
        <ResizablePanelGroup direction="vertical" className="h-full">
          {tabStack.map((tab, index) => (
            <Fragment key={tab.id}>
              {index > 0 && (
                <ResizableHandle
                  withHandle
                  className="bg-border hover:bg-primary/20 transition-colors h-px"
                />
              )}
              <ResizablePanel
                minSize={15}
                defaultSize={100 / tabStack.length}
                className="flex flex-col overflow-hidden"
              >
                <ContextPanel
                  tab={tab}
                  projectTree={filteredProjectData ?? projectData}
                  isActive={tab.id === activeTabId}
                  onActivate={() => setActiveTabId(tab.id)}
                  onClose={() => destroyTabBranch(tab.id)}
                />
              </ResizablePanel>
            </Fragment>
          ))}
        </ResizablePanelGroup>
      </div>

      {/* 3. Global Modals/Dialogs */}
      <SidebarDialogs />
    </div>
  );
});

export default SideBar;

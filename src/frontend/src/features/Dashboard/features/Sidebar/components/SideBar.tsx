import { memo } from "react";
import { SidebarHeader } from "./SidebarHeader";

import { TabContextStack } from "./TabContextStack";

import { useSidebarData } from "../hooks/useSidebarData";
import useProjectStore from "../../../store/useProjectStore";

/**
 * Main Sidebar Container
 * Manages the layout of project tree, search, and other sidebar features.
 * Supports hierarchical Context Panels.
 */
export const SideBar = memo(function SideBar() {
  const projectData = useProjectStore((s) => s.projectData);
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
        <TabContextStack
          projectData={projectData}
          filteredProjectData={filteredProjectData}
        />
      </div>

  
    </div>
  );
});

export default SideBar;

import { memo } from "react";
import { useParams } from "react-router-dom";
import { SidebarHeader } from "./SidebarHeader";
import { SidebarProjectSkeleton } from "./SidebarProjectSkeleton";
import { TabContextStack } from "./TabContextStack";

import { useSidebarData } from "../hooks/useSidebarData";
import useProjectStore from "../../../store/useProjectStore";

/**
 * Main Sidebar Container
 * Manages the layout of project tree, search, and other sidebar features.
 * Supports hierarchical Context Panels.
 */
export const SideBar = memo(function SideBar() {
  const { projectId } = useParams();
  const projectKey = projectId ? `ProjectSchema/${projectId}` : "";
  const projectData = useProjectStore((s) => s.projectData);
  const {
    filteredProjectData,
    searchQuery,
    setSearchQuery,
    isStructurePending,
  } = useSidebarData();

  const structureOutOfSync =
    Boolean(projectKey) &&
    Boolean(projectData) &&
    projectData.id !== projectKey;
  const showStructureSkeleton =
    Boolean(projectKey) && (isStructurePending || structureOutOfSync);

  if (showStructureSkeleton) {
    return (
      <div className="flex flex-col h-full bg-sidebar border-r overflow-hidden">
        <div className="flex-none transition-all duration-300">
          <SidebarHeader
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            loading
          />
        </div>
        <div className="flex-1 min-h-0 overflow-hidden p-0">
          <SidebarProjectSkeleton />
        </div>
      </div>
    );
  }

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

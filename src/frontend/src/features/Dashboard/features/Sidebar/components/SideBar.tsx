import { SidebarDialogs } from "./SidebarDialogs";
import ProjectTree from "./ProjectTree";
import { SearchInput } from "./SearchInput";
import { useTreeFilter } from "../hooks/useTreeFilter";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { AnyNodeTree } from "@/types/project";

export default function SideBar() {
  const projectData = useProjectStore((s) => s.projectData);
  const { filteredNodes, searchQuery, setSearchQuery } = useTreeFilter(
    projectData?.children as AnyNodeTree[]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search files..."
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto">
        <ProjectTree projectTree={filteredNodes} />
      </div>

      {/* Dialogs - Single instance at root */}
      <SidebarDialogs />
    </div>
  );
}

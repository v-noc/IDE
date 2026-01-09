// Sidebar/components/SideBar.tsx
import { useTreeFilter } from "../hooks/useTreeFilter";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { ProjectTree } from "./ProjectTree";
import { SearchInput } from "./SearchInput";

export default function SideBar() {
  const projectData = useProjectStore((s) => s.projectData);
  const { searchQuery, setSearchQuery, filteredNodes } = useTreeFilter(
    projectData?.children
  );

  return (
    <div className="h-full flex flex-col">
      {/* Header with search */}
      <div className="p-3 border-b">
        <SearchInput
          value={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search..."
        />
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-auto">
        <ProjectTree nodes={filteredNodes} />
      </div>
    </div>
  );
}

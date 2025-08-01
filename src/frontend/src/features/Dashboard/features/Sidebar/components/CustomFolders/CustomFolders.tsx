import { useState } from "react";
import { Input } from "@/components/ui/input";
import { TreeNode } from "../TreeNode";
import useProjectStore from "@/stores/useProjectStore";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";

const CustomFolders = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const { virtualFolderStructures } = useProjectStore();

  const filteredFolders = virtualFolderStructures.filter((folder) =>
    folder.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-2">
      <Input
        type="text"
        placeholder="Search..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full"
      />
      {filteredFolders.map((folder: ProjectTreeResponse) => (
        <TreeNode key={folder.key} node={folder} />
      ))}
    </div>
  );
};

export default CustomFolders;

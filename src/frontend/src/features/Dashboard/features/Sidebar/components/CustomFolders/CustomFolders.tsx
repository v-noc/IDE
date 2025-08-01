import { useState } from "react";
import { Input } from "@/components/ui/input";
import { TreeNode } from "../TreeNode";
import CreateVirtualFolderDialog from "./CreateVirtualFolderDialog";
import useProjectStore from "@/stores/useProjectStore";

const CustomFolders = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const { virtualFolderStructures } = useProjectStore();

  const filteredFolders = virtualFolderStructures.filter((folder) =>
    folder.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div className="text-xs font-medium text-gray-600 px-2 flex items-center justify-between">
        Custom Folders
        <CreateVirtualFolderDialog />
      </div>
      <div className="p-2">
        <Input
          placeholder="Filter folders..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      <div className="flex flex-col gap-2">
        {filteredFolders.map((folder) => (
          <TreeNode key={folder.key} node={folder} />
        ))}
      </div>
    </div>
  );
};

export default CustomFolders;

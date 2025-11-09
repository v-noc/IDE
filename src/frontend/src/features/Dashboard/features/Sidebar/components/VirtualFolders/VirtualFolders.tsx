import { useState } from "react";
import { Input } from "@/components/ui/input";
// import { TreeNode } from "../TreeNode";
// import { useGetVirtualFolders } from "@/features/Dashboard/service/useProject";
// import { useParams } from "react-router-dom";
// import { Skeleton } from "@/components/ui/skeleton";

const VirtualFolders = () => {
  const [searchTerm, setSearchTerm] = useState("");
  // const { projectId } = useParams();
  // const { data: virtualFolders, isLoading } = useGetVirtualFolders(
  //   projectId || ""
  // );

  // const filteredFolders = useMemo(() => {
  //   if (!virtualFolders) {
  //     return [];
  //   }
  //   return virtualFolders.filter((folder) =>
  //     folder.name.toLowerCase().includes(searchTerm.toLowerCase())
  //   );
  // }, [virtualFolders, searchTerm]);

  // if (isLoading) {
  //   return (
  //     <div className="space-y-2">
  //       <Skeleton className="h-8 w-full" />
  //       <Skeleton className="h-8 w-full" />
  //       <Skeleton className="h-8 w-full" />
  //     </div>
  //   );
  // }

  return (
    <div className="flex flex-col gap-2">
      <Input
        type="text"
        placeholder="Search virtual folders..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="w-full"
      />
      {/* {filteredFolders && filteredFolders.length > 0 ? (
        <div className="space-y-1">
          {filteredFolders.map((folder) => (
            <TreeNode key={folder.key} node={folder} />
          ))}
        </div>
      ) : (
        <div className="text-sm text-muted-foreground py-4 text-center">
          {searchTerm
            ? "No virtual folders found"
            : "No virtual folders created yet"}
          <div className="text-xs mt-2 opacity-60">
            Click the + button above to create your first virtual folder
          </div>
        </div>
      )} */}
    </div>
  );
};

export default VirtualFolders;

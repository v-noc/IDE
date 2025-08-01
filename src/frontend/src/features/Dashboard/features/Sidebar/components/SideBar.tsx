import { Link, useParams } from "react-router";
import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import ProjectTree from "./ProjectTree";

import CreateFolderStructure from "./CreateFolderStructure";
import { Separator } from "@/components/ui/separator";

const SideBar = () => {
  const { projectId } = useParams();

  const { data } = useGetProjectTreeWithKeyProject({
    key: projectId || "",
  });
  console.log(data);
  return (
    <div className=" h-full w-full flex flex-col gap-2">
      <Link to="/">
        <div className="text-2xl font-bold flex items-center  h-[57px] bg-sky-600 text-white">
          <span className="pl-4 text-white  ">v-noc</span>
        </div>
      </Link>
      <div className="flex flex-col gap-2 p-2">
        <div className="text-xs font-medium text-gray-600 px-2 flex items-center justify-between">
          Project Files
        </div>
        <div>{data && <ProjectTree projectTree={data} />}</div>
        <Separator className="my-2" />
        <div className="text-xs font-medium text-gray-600 px-2 flex items-center justify-between">
          Custom Folders & Files
          <CreateFolderStructure />
        </div>
      </div>
    </div>
  );
};

export default SideBar;

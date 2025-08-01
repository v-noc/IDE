import { Link, useParams } from "react-router";
import { useGetProjectTreeWithKeyProject } from "@/features/Dashboard/service/useProject";
import ProjectTree from "./ProjectTree";

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

      <div className="p-2">{data && <ProjectTree projectTree={data} />}</div>
    </div>
  );
};

export default SideBar;

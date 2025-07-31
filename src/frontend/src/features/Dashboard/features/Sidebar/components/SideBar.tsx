import ProjectTree from "./ProjectTree";

const SideBar = () => {
  return (
    <div className=" h-full w-full flex flex-col gap-4">
      <div className="text-2xl font-bold flex mb-4 items-center  h-[57px] bg-sky-600 text-white">
        <span className="pl-4 text-white  ">v-noc</span>
      </div>
      <div className="p-2">
        <ProjectTree />
      </div>
    </div>
  );
};

export default SideBar;

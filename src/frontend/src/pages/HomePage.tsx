import { useState } from "react";
import Header from "@/features/Home/componets/Header";
import SearchAndViewController from "@/features/Home/componets/SearchAndViewController";
import ProjectList from "@/features/Home/componets/ProjectList";
import { useProjects } from "@/features/Home/hook/useProject";

const HomePage = () => {
  const { data: projects, isLoading } = useProjects();

  const [viewMode, setViewMode] = useState<"list" | "grid">("grid");

  return (
    <div className="min-h-screen bg-[#f9f9f9] p-6 w-full">
      <div className="max-w-screen w-full mx-auto">
        <Header />
        <SearchAndViewController
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
        {isLoading ? (
          <div>Loading...</div>
        ) : (
          <ProjectList viewMode={viewMode} projects={projects || []} />
        )}
      </div>
    </div>
  );
};

export default HomePage;

import { useState } from "react";
import Header from "@/features/Home/componets/Header";
import SearchAndViewController from "@/features/Home/componets/SearchAndViewController";
import ProjectList from "@/features/Home/componets/ProjectList";
import { useProjects } from "@/services/projectService";

const HomePage = () => {
  const { data: projects, error, isLoading } = useProjects();
  console.log(error);
  const [viewMode, setViewMode] = useState<"list" | "grid">("grid");

  return (
    <div className="min-h-screen bg-background p-6 w-full">
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

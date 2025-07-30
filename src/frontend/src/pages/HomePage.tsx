import Header from "@/features/Home/componets/Header";
import SearchAndViewController from "@/features/Home/componets/SearchAndViewController";
import ProjectList from "@/features/Home/componets/ProjectList";
import { useState } from "react";
import type { Project } from "@/types/project";

const HomePage = () => {
  const [projects, setProjects] = useState<Project[]>([
    {
      id: "1",
      name: "E-commerce Platform",
      path: "/Users/developer/projects/ecommerce-platform",
      description: "Full-stack e-commerce solution with React and Node.js",
      createdDate: "2024-01-15",
      lastModified: "2024-01-28",
    },
    {
      id: "2",
      name: "Task Manager API",
      path: "/Users/developer/projects/task-manager-api",
      description: "RESTful API for task management with authentication",
      createdDate: "2024-01-10",
      lastModified: "2024-01-25",
    },
    {
      id: "3",
      name: "Mobile Weather App",
      path: "/Users/developer/projects/weather-app-mobile",
      description: "Cross-platform weather application built with React Native",
      createdDate: "2024-01-05",
      lastModified: "2024-01-20",
    },
  ]);

  const [viewMode, setViewMode] = useState<"list" | "grid">("grid");

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto">
        <Header />
        <SearchAndViewController
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
        <ProjectList viewMode={viewMode} projects={projects} />
      </div>
    </div>
  );
};

export default HomePage;

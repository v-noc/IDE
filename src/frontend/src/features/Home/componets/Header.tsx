import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import CreateProjectDialog from "./CreateProjectDialog";

// import { useCreateProject } from "@/services/projectService";

// interface ImportProject {}

const Header = () => {
  return (
    <div className="flex items-center justify-between mb-8">
      <h1 className="text-3xl font-bold">Projects</h1>
      <div className="flex items-center gap-3">
        <CreateProjectDialog
          trigger={
            <Button className="gap-2 ">
              <Plus className="h-4 w-4" />
              Create Project
            </Button>
          }
          title="Create New Project"
          description="Create a new project from your local computer"
        />
      </div>
    </div>
  );
};

export default Header;

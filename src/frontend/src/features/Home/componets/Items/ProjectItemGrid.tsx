import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Calendar, Clock, Edit, Folder, MoreHorizontal } from "lucide-react";
import { formatDate } from "date-fns";
import type { Project } from "@/types/project";
import { truncatePath } from "@/utils";

const ProjectItemGrid = ({
  project,
  setEditingProject,
}: {
  project: Project;
  setEditingProject: (project: Project) => void;
}) => {
  return (
    <Card key={project.key} className="hover:shadow-md transition-shadow">
      <CardHeader className="p-0 pb-3 ">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <Folder className="h-5 w-5 text-muted-foreground flex-shrink-0" />
            <CardTitle className="text-lg truncate">{project.name}</CardTitle>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setEditingProject(project)}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-3 font-mono break-all">
          {truncatePath(project.path, 40)}
        </p>
        <CardDescription className="mb-4 line-clamp-2">
          {project.description}
        </CardDescription>
        <div className="space-y-1 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            Created: {formatDate(project.createdDate, "MM/dd/yyyy")}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Modified: {formatDate(project.lastModified, "MM/dd/yyyy")}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ProjectItemGrid;

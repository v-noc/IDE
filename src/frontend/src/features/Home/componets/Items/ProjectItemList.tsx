import { Card, CardContent } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Calendar, Clock, Edit, Folder, MoreHorizontal } from "lucide-react";
import { formatDate } from "date-fns";
import type { Project } from "@/types/project";
import { truncatePath } from "@/utils";
import { Button } from "@/components/ui/button";

const ProjectItem = ({
  project,
  setEditingProject,
}: {
  project: Project;
  setEditingProject: (project: Project) => void;
}) => {
  return (
    <Card key={project.id} className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <Folder className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              <h3 className="text-lg font-semibold truncate">{project.name}</h3>
              {/* <Badge variant="secondary">{project.type}</Badge> */}
            </div>
            <p className="text-sm text-muted-foreground mb-2 font-mono">
              {truncatePath(project.path)}
            </p>
            <p className="text-sm text-muted-foreground mb-3">
              {project.description}
            </p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                Created: {formatDate(project.createdDate, "MM/dd/yyyy")}
              </div>
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Modified: {formatDate(project.lastModified, "MM/dd/yyyy")}
              </div>
            </div>
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
      </CardContent>
    </Card>
  );
};

export default ProjectItem;

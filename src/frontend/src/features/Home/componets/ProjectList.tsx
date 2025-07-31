import { Button } from "@/components/ui/button";
import {
  Card,
  CardTitle,
  CardHeader,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import { Calendar, Clock, Edit, Folder, MoreHorizontal } from "lucide-react";
import { useNavigate } from "react-router";
import { truncatePath } from "@/utils";
import type { Project } from "@/types/project";

const ProjectList = ({
  viewMode,
  projects,
}: {
  viewMode: "list" | "grid";
  projects: Project[];
}) => {
  const navigate = useNavigate();
  if (viewMode === "grid") {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <Card
            key={project.id}
            className="hover:shadow-md transition-shadow p-4 cursor-pointer"
            onClick={() => navigate(`/project/${project.id}`)}
          >
            <CardHeader className="p-0 ">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Folder className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <CardTitle className="text-lg truncate">
                    {project.name}
                  </CardTitle>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                    //   onClick={() => setEditingProject(project)}
                    >
                      <Edit className="h-4 w-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <p className="text-xs text-muted-foreground mb-3 font-mono break-all">
                {truncatePath(project.path, 40)}
              </p>
              <CardDescription className="mb-4 line-clamp-2">
                {/* {project.description} */}
              </CardDescription>
              <div className="space-y-1 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {/* Created: {formatDate(project.createdDate, "MM/dd/yyyy")} */}
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {/* Modified: {formatDate(project.lastModified, "MM/dd/yyyy")} */}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {projects.map((project) => (
        <Card
          key={project.id}
          className="hover:shadow-md transition-shadow p-4 cursor-pointer"
          onClick={() => navigate(`/project/${project.id}`)}
        >
          <CardContent className="p-2">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <Folder className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                  <h3 className="text-lg font-semibold truncate">
                    {project.name}
                  </h3>
                </div>
                <p className="text-sm text-muted-foreground mb-2 font-mono">
                  {truncatePath(project.path)}
                </p>
                <p className="text-sm text-muted-foreground mb-3">
                  {/* {project.description} */}
                </p>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {/* Created: {formatDate(project.createdDate, "MM/dd/yyyy")} */}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {/* Modified: {formatDate(project.lastModified, "MM/dd/yyyy")} */}
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
                  <DropdownMenuItem>
                    <Edit className="h-4 w-4 mr-2" />
                    Edit
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ProjectList;

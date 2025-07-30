import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { useForm } from "react-hook-form";
import FileAndFolderSelector from "@/components/FileAndFolderSelector";

interface ProjectDialogProps {
  trigger?: React.ReactNode;
  onSubmit: (data: ProjectForm) => void;
  title: string;
  description: string;
}

interface ProjectForm {
  path: string;
  name: string;
  description: string;
}

const ProjectDialog = ({
  trigger,
  onSubmit,
  title,
  description,
}: ProjectDialogProps) => {
  const { register, handleSubmit, setValue } = useForm<ProjectForm>();
  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue("path", e.target.value);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="import-path">Project Path</Label>
              <div className="flex gap-2">
                <Input
                  id="import-path"
                  placeholder="/path/to/existing/project"
                  // value={importProject.path}
                  onChange={(e) =>
                    setImportProject({
                      ...importProject,
                      path: e.target.value,
                    })
                  }
                  className="flex-1"
                />
                <FileAndFolderSelector
                  handleFolderSelect={handleFolderSelect}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Click the folder icon to browse and select an existing project
                folder or file
              </p>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="import-name">Project Name</Label>
              <Input
                id="import-name"
                placeholder="My Existing Project"
                {...register("name")}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="import-description">Description</Label>
              <Textarea
                id="import-description"
                placeholder="Brief description of the project..."
                {...register("description")}
              />
            </div>
          </div>
          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              // onClick={() => setIsImportDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit">Import Project</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default ProjectDialog;

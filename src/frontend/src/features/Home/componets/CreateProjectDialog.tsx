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
import * as z from "zod";
import { useForm } from "react-hook-form";
import FileAndFolderSelector from "@/components/FileAndFolderSelector";
import { useCreateProject } from "@/features/Home/hook/useProject";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";
import { parse } from "toml";

import { extractFieldErrors } from "@/utils/errorMessagextractor";

interface CreateProjectDialogProps {
  trigger?: React.ReactNode;

  title: string;
  description: string;
}

const formSchema = z.object({
  path: z.string().min(1, "Path is required"),
  name: z.string().min(3, "String should have at least 3 characters"),
  description: z.string(),
});

type FormValues = z.infer<typeof formSchema>;

const CreateProjectDialog = ({
  trigger,

  title,
  description,
}: CreateProjectDialogProps) => {
  const { mutate: createProject, isPending } = useCreateProject();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    setValue,

    setError,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      path: "",
      name: "",
      description: "",
    },
  });

  const onSubmit = (data: FormValues) => {
    createProject(data, {
      onSuccess(data) {
        const key = data._key;
        console.log("project ket", key);
        setTimeout(() => navigate(`/project/${key}`));
      },
      onError: (error) => {
        const fieldErrors = extractFieldErrors(error);
        if (fieldErrors.length === 0) return;
        fieldErrors.forEach((fe) => {
          const field = fe.field as keyof FormValues;
          setError(field, { type: "server", message: fe.message });
        });
      },
    });
  };

  const handleFolderSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Get the folder path from the first file
      const firstFile = files[0];
      const folderPath = firstFile.webkitRelativePath.split("/")[0];

      // Extract folder name from path
      const folderName = folderPath.split(/[\\/]/).pop() || folderPath;

      // Get all files in the folder
      const allFiles: File[] = Array.from(files);

      console.log("Folder name:", folderName);
      console.log("Folder path:", folderPath);
      console.log("All files in folder:", allFiles);
      console.log("File count:", allFiles.length);

      // You can also get file details
      const fileDetails = allFiles.map((file) => ({
        name: file.name,
        path: file.webkitRelativePath,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
      }));

      const tomlFile = fileDetails.find((file) => file.name === "v-noc.toml");
      if (tomlFile) {
        // Find the actual File object from the files array
        const tomlFileObject = allFiles.find(
          (file) => file.name === "v-noc.toml"
        );
        if (tomlFileObject) {
          const tomlContent = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
              const content = e.target?.result as string;
              resolve(content);
            };
            reader.onerror = () => reject(new Error("Failed to read file"));
            reader.readAsText(tomlFileObject);
          });

          console.log("TOML content:", tomlContent);
          try {
            const tomlData = parse(tomlContent);
            // Set the folder path in the form
            setValue("path", tomlData.pwd);
            setValue("name", tomlData.name);
            setValue("description", tomlData.description);
            console.log("TOML data:", tomlData);
          } catch (error) {
            console.error("Failed to parse TOML:", error);
          }
        }
      }
      console.log("File details:", fileDetails);
    }
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
                  {...register("path")}
                  className="flex-1"
                />
                <FileAndFolderSelector
                  handleFolderSelect={handleFolderSelect}
                />
              </div>
              {errors.path?.message && (
                <p className="text-xs text-red-500">{errors.path.message}</p>
              )}
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
              {errors.name?.message && (
                <p className="text-xs text-red-500">{errors.name.message}</p>
              )}
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
            <Button type="submit" disabled={isPending}>
              {isPending ? "Creating..." : "Create Project"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateProjectDialog;

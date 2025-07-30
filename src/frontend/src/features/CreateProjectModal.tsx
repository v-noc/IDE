import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useCreateProject } from "../services/projectService";
import { useEffect } from "react";

const formSchema = z.object({
  path: z.string().min(1, "Path is required"),
  name: z.string(),
});

type FormValues = z.infer<typeof formSchema>;

export const CreateProjectModal = () => {
  const { mutate: createProject, isSuccess } = useCreateProject();
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      path: "",
      name: "",
    },
  });

  const path = watch("path");

  useEffect(() => {
    if (path) {
      const name = path.split(/[\\/]/).pop() || "";
      setValue("name", name);
    }
  }, [path, setValue]);

  useEffect(() => {
    if (isSuccess) {
      reset();
    }
  }, [isSuccess, reset]);

  const onSubmit = (data: FormValues) => {
    createProject(data);
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create Project</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create a new project</DialogTitle>
          <DialogDescription>
            Enter the path to your project directory. The project name will be
            derived from the path.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="path">Path</Label>
            <Input id="path" {...register("path")} />
            {errors.path && (
              <p className="text-red-500 text-sm">{errors.path.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="name">Name</Label>
            <Input id="name" {...register("name")} readOnly />
          </div>
          <Button type="submit">Create</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

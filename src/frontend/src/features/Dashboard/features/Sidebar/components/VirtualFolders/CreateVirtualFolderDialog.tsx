import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { PlusIcon } from "lucide-react";
import z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useMutation } from "@tanstack/react-query";
import API_ROUTES from "@/lib/apiRoutes";

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateVirtualFolderRequest {
  name: string;
  description?: string;
}

const CreateVirtualFolderDialog = () => {
  const [isOpen, setOpen] = useState(false);
  const { projectData } = useProjectStore();
  const queryClient = useQueryClient();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });

  // Create mutation for virtual folder creation
  const createVirtualFolderMutation = useMutation({
    mutationFn: async (requestData: CreateVirtualFolderRequest) => {
      if (!projectData?.key) {
        throw new Error("No project selected");
      }

      return await fetch(
        `${import.meta.env.VITE_API_BASE_URL || "/api/core"}${
          API_ROUTES.VIRTUAL_FOLDER
        }${projectData.key}/virtual-folder`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestData),
        }
      ).then(async (response) => {
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}`);
        }
        return response.json();
      });
    },
    onSuccess: () => {
      // Invalidate and refetch project tree
      queryClient.invalidateQueries({
        queryKey: ["projectTree", projectData?.key],
      });
      toast.success("Virtual folder created successfully");
      setOpen(false);
      form.reset();
    },
    onError: (error) => {
      console.error("Failed to create virtual folder:", error);
      toast.error(`Failed to create virtual folder: ${error.message}`);
    },
  });

  const onSubmit = async (data: FormValues) => {
    if (!projectData?.key) {
      toast.error("No project selected");
      return;
    }

    console.log("Creating virtual folder with data:", data);

    createVirtualFolderMutation.mutate({
      name: data.name,
      description: data.description || undefined,
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="icon" className="cursor-pointer ">
          <PlusIcon className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Virtual Folder</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="Enter folder name" />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (Optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Enter folder description"
                      rows={3}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button
              type="submit"
              disabled={createVirtualFolderMutation.isPending}
              className="w-full"
            >
              {createVirtualFolderMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateVirtualFolderDialog;

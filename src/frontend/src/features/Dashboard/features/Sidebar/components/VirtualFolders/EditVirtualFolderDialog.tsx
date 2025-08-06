import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import {
  useUpdateVirtualFolder,
  type ProjectTreeResponse,
  type VirtualFolderUpdateRequest,
} from "@/features/Dashboard/service/useProject";
import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface EditVirtualFolderDialogProps {
  isOpen: boolean;
  onClose: () => void;
  node: ProjectTreeResponse | undefined;
}

const EditVirtualFolderDialog = ({
  isOpen,
  onClose,
  node,
}: EditVirtualFolderDialogProps) => {
  const { projectData } = useProjectStore();
  const queryClient = useQueryClient();

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: node?.name || "",
      description: node?.description || "",
    },
  });

  const updateVirtualFolderMutation = useUpdateVirtualFolder(
    projectData?.key || "",
    node?.key || ""
  );

  // Reset form when node changes
  useEffect(() => {
    form.reset({
      name: node?.name || "",
      description: node?.description || "",
    });
  }, [node, form]);

  const onSubmit = async (data: FormValues) => {
    if (!projectData?.key || !node?.key) {
      toast.error("No project or folder selected");
      return;
    }

    try {
      const updateData: VirtualFolderUpdateRequest = {
        name: data.name,
        description: data.description || undefined,
      };

      await updateVirtualFolderMutation.mutateAsync(updateData);

      // Invalidate and refetch project tree
      await queryClient.invalidateQueries({
        queryKey: ["projectTree", projectData.key],
      });

      toast.success("Virtual folder updated successfully");
      onClose();
    } catch (error) {
      console.error("Failed to update virtual folder:", error);
      toast.error("Failed to update virtual folder");
    }
  };

  if (!node) {
    return null;
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Virtual Folder</DialogTitle>
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
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateVirtualFolderMutation.isPending}
              >
                {updateVirtualFolderMutation.isPending
                  ? "Updating..."
                  : "Update"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default EditVirtualFolderDialog;

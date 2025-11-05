import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import type { AnyNodeTree } from "@/types/project";
import { useCreateGroup } from "../service/useGroup";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

interface CreateGroupsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  initialChildren: AnyNodeTree[];
  project_key: string;
  parent_node_id: string;
}

const CreateGroupsDialog = ({
  isOpen,
  onClose,
  initialChildren,
  project_key,
  parent_node_id,
}: CreateGroupsDialogProps) => {
  const { mutate: createGroup, isPending } = useCreateGroup(
    parent_node_id,
    project_key
  );
  const formSchema = z.object({
    name: z.string().min(1, "Name is required").max(100),
    description: z.string().max(500),
    children_ids: z.array(z.string().min(1)),
  });
  type CreateGroupForm = z.infer<typeof formSchema>;

  const form = useForm<CreateGroupForm>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      description: "",
      children_ids: initialChildren.map((child) => child._key),
    },
  });

  const onSubmit = (values: CreateGroupForm) => {
    createGroup(values, { onSuccess: onClose });
  };
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Group</DialogTitle>
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
                    <Input
                      placeholder="Enter group name"
                      {...field}
                      disabled={isPending}
                    />
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
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      rows={4}
                      placeholder="Optional description"
                      {...field}
                      disabled={isPending}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? "Creating..." : "Create"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateGroupsDialog;

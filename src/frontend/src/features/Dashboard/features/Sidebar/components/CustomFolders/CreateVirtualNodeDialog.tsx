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
import { useForm } from "react-hook-form";
import useProjectStore from "@/stores/useProjectStore";

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
});

type FormValues = z.infer<typeof formSchema>;
type NodeType = "file" | "folder";

interface CreateVirtualNodeDialogProps {
  parentId: string;
  isOpen: boolean;
  onClose: () => void;
  nodeType: NodeType;
}

const CreateVirtualNodeDialog = ({
  parentId,
  isOpen,
  onClose,
  nodeType,
}: CreateVirtualNodeDialogProps) => {
  const { addVirtualNode } = useProjectStore();
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
    },
  });

  const onSubmit = (data: FormValues) => {
    addVirtualNode(parentId, data.name, nodeType);
    onClose();
    form.reset();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            Create New {nodeType === "folder" ? "Folder" : "File"}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit">Create</Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};

export default CreateVirtualNodeDialog;

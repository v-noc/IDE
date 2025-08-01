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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { NodeType, useVirtualFolderStore } from "./useVirtualFolderStore";

const formSchema = z.object({
  name: z.string().min(1, "Name is required"),
  type: z.enum(["file", "folder"]),
});

type FormValues = z.infer<typeof formSchema>;

interface CreateVirtualNodeDialogProps {
  parentId: string;
  isOpen: boolean;
  onClose: () => void;
}

const CreateVirtualNodeDialog = ({
  parentId,
  isOpen,
  onClose,
}: CreateVirtualNodeDialogProps) => {
  const { addNode } = useVirtualFolderStore();
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      type: "file",
    },
  });

  const onSubmit = (data: FormValues) => {
    addNode(parentId, data.name, data.type as NodeType);
    onClose();
    form.reset();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New</DialogTitle>
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
            <FormField
              control={form.control}
              name="type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="file">File</SelectItem>
                      <SelectItem value="folder">Folder</SelectItem>
                    </SelectContent>
                  </Select>
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

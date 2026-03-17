import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export interface PlaygroundFormValues {
  name: string;
  description: string;
  relative_path: string;
  executable_path: string;
  filename: string;
}

interface PlaygroundFormDialogProps {
  open: boolean;
  isUpdate: boolean;
  values: PlaygroundFormValues;
  isSubmitting?: boolean;
  onOpenChange: (open: boolean) => void;
  onChange: (next: PlaygroundFormValues) => void;
  onSubmit: () => void;
}

export default function PlaygroundFormDialog({
  open,
  isUpdate,
  values,
  isSubmitting = false,
  onOpenChange,
  onChange,
  onSubmit,
}: PlaygroundFormDialogProps) {
  const title = isUpdate ? "Update Playground" : "Create Playground";
  const submitLabel = isUpdate ? "Update" : "Create";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="playgroundName">Name</Label>
            <Input
              id="playgroundName"
              value={values.name}
              onChange={(e) => onChange({ ...values, name: e.target.value })}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="playgroundDescription">Description</Label>
            <Input
              id="playgroundDescription"
              value={values.description}
              onChange={(e) =>
                onChange({ ...values, description: e.target.value })
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="playgroundRelativePath">Relative path</Label>
            <Input
              id="playgroundRelativePath"
              value={values.relative_path}
              onChange={(e) =>
                onChange({ ...values, relative_path: e.target.value })
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="playgroundExecutablePath">Executable path</Label>
            <Input
              id="playgroundExecutablePath"
              value={values.executable_path}
              onChange={(e) =>
                onChange({ ...values, executable_path: e.target.value })
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="playgroundFilename">Filename</Label>
            <Input
              id="playgroundFilename"
              value={values.filename}
              onChange={(e) => onChange({ ...values, filename: e.target.value })}
            />
          </div>
        </div>
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button type="button" onClick={onSubmit} disabled={isSubmitting}>
            {submitLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

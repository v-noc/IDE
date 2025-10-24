import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  examplesPath: string;
  commandPrefix: string;
  onChangeExamplesPath: (value: string) => void;
  onChangeCommandPrefix: (value: string) => void;
}

export default function SettingsDialog({
  open,
  onOpenChange,
  examplesPath,
  commandPrefix,
  onChangeExamplesPath,
  onChangeCommandPrefix,
}: SettingsDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Playground Settings</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="examplesPath">
              Examples path (relative to repo root)
            </Label>
            <Input
              id="examplesPath"
              placeholder="e.g. examples,src/examples or leave it blank for root path"
              value={examplesPath}
              onChange={(e) => onChangeExamplesPath(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="commandPrefix">Run command prefix</Label>
            <Input
              id="commandPrefix"
              placeholder="e.g. python or npm run"
              value={commandPrefix}
              onChange={(e) => onChangeCommandPrefix(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="button" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

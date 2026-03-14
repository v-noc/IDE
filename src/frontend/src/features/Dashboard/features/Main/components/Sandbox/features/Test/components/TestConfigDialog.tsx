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
import type { TestConfig } from "../types";

interface TestConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  config: TestConfig;
  isConfigCreated: boolean;
  onChangeConfig: (next: TestConfig) => void;
  onSave: () => void;
}

export default function TestConfigDialog({
  open,
  onOpenChange,
  config,
  isConfigCreated,
  onChangeConfig,
  onSave,
}: TestConfigDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isConfigCreated ? "Edit Test Configuration" : "Create Test Configuration"}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="testFramework">Test framework</Label>
            <Input
              id="testFramework"
              placeholder="e.g. pytest"
              value={config.framework}
              onChange={(e) =>
                onChangeConfig({
                  ...config,
                  framework: e.target.value,
                })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="testsPath">Tests path</Label>
            <Input
              id="testsPath"
              placeholder="e.g. src/backend/tests"
              value={config.testsPath}
              onChange={(e) =>
                onChangeConfig({
                  ...config,
                  testsPath: e.target.value,
                })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="commandPrefix">Run command prefix</Label>
            <Input
              id="commandPrefix"
              placeholder="e.g. python -m"
              value={config.commandPrefix}
              onChange={(e) =>
                onChangeConfig({
                  ...config,
                  commandPrefix: e.target.value,
                })
              }
            />
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="button" onClick={onSave}>
            {isConfigCreated ? "Update configuration" : "Create configuration"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

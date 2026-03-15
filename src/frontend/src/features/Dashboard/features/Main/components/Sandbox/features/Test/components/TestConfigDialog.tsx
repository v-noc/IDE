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
            {isConfigCreated
              ? "Edit Test Configuration"
              : "Create Test Configuration"}
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-2">
          <div className="grid gap-2">
            <Label htmlFor="enabled">Test execution</Label>
            <div className="flex items-center justify-between rounded-md border px-3 py-2">
              <span className="text-sm text-slate-700">Enable test execution</span>
              <input
                id="enabled"
                type="checkbox"
                checked={config.enabled}
                onChange={(e) =>
                  onChangeConfig({
                    ...config,
                    enabled: e.target.checked,
                  })
                }
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label htmlFor="testsPath">Test root path</Label>
            <Input
              id="testsPath"
              placeholder="e.g. src/backend/tests"
              value={config.testRoot}
              onChange={(e) =>
                onChangeConfig({
                  ...config,
                  testRoot: e.target.value,
                })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="testArgs">Test arguments</Label>
            <Input
              id="testArgs"
              placeholder="e.g. -q -k smoke"
              value={config.testArgs}
              onChange={(e) =>
                onChangeConfig({
                  ...config,
                  testArgs: e.target.value,
                })
              }
            />
          </div>

          <div className="grid gap-2">
            <Label htmlFor="executablePath">Python executable path</Label>
            <Input
              id="executablePath"
              placeholder="e.g. .venv/bin/python"
              value={config.executablePath}
              onChange={(e) =>
                onChangeConfig({
                  ...config,
                  executablePath: e.target.value,
                })
              }
            />
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
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

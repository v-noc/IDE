import { Button } from "@/components/ui/button";
import { Play, Settings2 } from "lucide-react";

interface RunToolbarProps {
  onRun: () => void;
  isRunning?: boolean;
  onOpenSettings?: () => void;
  className?: string;
}

export default function RunToolbar({
  onRun,
  isRunning = false,
  onOpenSettings,
  className,
}: RunToolbarProps) {
  return (
    <div className={className}>
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium text-muted-foreground">
          Playground
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={onOpenSettings}>
            <Settings2 className="mr-2 h-4 w-4" />
            Settings
          </Button>
          <Button size="sm" onClick={onRun} disabled={isRunning}>
            <Play className="mr-2 h-4 w-4" />
            {isRunning ? "Running..." : "Run"}
          </Button>
        </div>
      </div>
    </div>
  );
}

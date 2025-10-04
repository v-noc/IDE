import { Button } from "@/components/ui/button";
import { Play } from "lucide-react";

interface RunToolbarProps {
  onRun: () => void;
  isRunning?: boolean;
  className?: string;
}

export default function RunToolbar({
  onRun,
  isRunning = false,
  className,
}: RunToolbarProps) {
  return (
    <div className={className}>
      <div className="flex items-center justify-between">
        <div className="text-sm font-medium text-muted-foreground">
          Playground
        </div>
        <Button size="sm" onClick={onRun} disabled={isRunning}>
          <Play className="mr-2 h-4 w-4" />
          {isRunning ? "Running..." : "Run"}
        </Button>
      </div>
    </div>
  );
}

import { Button } from "@/components/ui/button";
import { Play, Settings } from "lucide-react";

export type SandboxToolbarVariant = "playground" | "test" | "mode-only";

interface SandboxToolbarProps {
  variant: SandboxToolbarVariant;
  modeLabel?: string;
  isRunning: boolean;
  onRun: () => void;
  onOpenSettings: () => void;
}

export function SandboxToolbar({
  variant,
  modeLabel = "Mode",
  isRunning,
  onRun,
  onOpenSettings,
}: SandboxToolbarProps) {
  if (variant === "mode-only") {
    const label =
      modeLabel.charAt(0).toUpperCase() + modeLabel.slice(1).toLowerCase();
    return (
      <div className="flex items-center px-3 h-full">
        <span className="text-[10px] font-semibold text-muted-foreground/60 uppercase tracking-widest">
          {label} Mode
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 h-full pr-3">
      <Button
        size="sm"
        onClick={onRun}
        disabled={isRunning}
        className="h-7 min-w-[72px] gap-1.5 rounded-md bg-emerald-600 px-3 text-xs font-medium text-white shadow-sm hover:bg-emerald-700 focus-visible:ring-emerald-500/50 disabled:opacity-70"
      >
        <Play className="size-3.5 shrink-0 fill-current" />
        {isRunning ? "Running..." : variant === "test" ? "Run tests" : "Run"}
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={onOpenSettings}
        className="size-7 shrink-0 rounded-md p-0 border border-input/80 hover:bg-muted/60 hover:border-input"
        aria-label="Open settings"
      >
        <Settings className="size-3.5 text-muted-foreground" />
      </Button>
    </div>
  );
}

import { getToolInfo } from "../tools/registry";
import type { ToolProgress as ToolProgressState } from "../stream/types";

interface ToolProgressProps {
  progress: ToolProgressState;
  toolId: string;
}

export function ToolProgress({ progress, toolId }: ToolProgressProps) {
  const unit = getToolInfo(toolId)?.unit ?? "steps";
  const pct =
    progress.total > 0
      ? Math.min(100, (100 * progress.done) / progress.total)
      : 0;

  return (
    <div className="space-y-2">
      <p className="font-agent-mono text-[11px] text-agent-text-muted">
        {progress.done} / {progress.total} {unit} · running…
      </p>
      <div className="h-[5px] overflow-hidden rounded-full bg-agent-bg-raised">
        <div
          className="agent-tool-progress-fill h-full rounded-full transition-[width] duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

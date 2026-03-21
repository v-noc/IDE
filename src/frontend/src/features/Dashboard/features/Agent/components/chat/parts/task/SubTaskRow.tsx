import { subTaskLabel } from "./subTaskLabel";
import { TaskStatusDot } from "./TaskStatusDot";
import { toVisualStatus } from "./taskStatus";
import type { TaskSubWire } from "./types";

export function SubTaskRow({ sub }: { sub: TaskSubWire }) {
  const status = toVisualStatus(sub.state);
  return (
    <div className="flex gap-2.5 rounded-lg border border-border/60 bg-background/50 py-2 pl-2 pr-2.5">
      <div className="pt-0.5">
        <TaskStatusDot status={status} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[11px] font-semibold leading-snug text-foreground">
          {subTaskLabel(sub)}
        </p>
        {sub.description ? (
          <p className="mt-0.5 text-[10px] leading-snug text-muted-foreground">
            {sub.description}
          </p>
        ) : null}
      </div>
    </div>
  );
}

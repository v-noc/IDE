import type { Task, AnchorSummary } from "@/types/tasks";
import { TaskTypeBadge } from "./TaskTypeBadge";
import { PriorityBars } from "./PriorityBars";
import { AnchorChip } from "./AnchorChip";

interface TaskCardProps {
  task: Task;
  anchorSummary?: AnchorSummary;
  isDragging?: boolean;
  onClick: () => void;
  onAnchorClick?: (nodeId: string) => void;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: () => void;
}

export function TaskCard({
  task,
  anchorSummary,
  isDragging,
  onClick,
  onAnchorClick,
  onDragStart,
  onDragEnd,
}: TaskCardProps) {
  const primaryAnchor = task.anchors[0];
  const anchorHot =
    primaryAnchor && anchorSummary?.nodes[primaryAnchor.node_id]?.hot;

  return (
    <div
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onClick={onClick}
      className={[
        "group cursor-grab rounded-md border bg-card p-2.5 text-sm shadow-sm transition-colors",
        "border-border hover:border-muted-foreground/40 hover:bg-accent/30",
        isDragging ? "opacity-35 border-dashed" : "",
        task.blocked ? "border-red-900/40" : "",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="font-medium leading-snug line-clamp-2">{task.title}</span>
        <PriorityBars priority={task.priority} />
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <TaskTypeBadge type={task.task_type} />
        {task.labels.map((label) => (
          <span
            key={label}
            className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
          >
            {label}
          </span>
        ))}
        {task.subtask_progress.total > 0 && (
          <span className="font-mono text-[10px] text-muted-foreground">
            ✓ {task.subtask_progress.done}/{task.subtask_progress.total}
          </span>
        )}
        {task.blocked && (
          <span className="rounded bg-red-950/50 px-1.5 py-0.5 text-[10px] text-red-400">
            ⊘ blocked
          </span>
        )}
      </div>

      {primaryAnchor && (
        <div className="mt-2" onClick={(e) => e.stopPropagation()}>
          <AnchorChip
            anchor={primaryAnchor}
            hot={anchorHot}
            onClick={() => onAnchorClick?.(primaryAnchor.node_id)}
          />
        </div>
      )}

      <div className="mt-1.5 font-mono text-[10px] text-muted-foreground">
        {task.key}
      </div>
    </div>
  );
}

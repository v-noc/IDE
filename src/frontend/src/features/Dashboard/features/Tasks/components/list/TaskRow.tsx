import type { AnchorSummary, BoardColumn, Task } from "@/types/tasks";
import { TaskTypeBadge } from "../TaskTypeBadge";
import { PriorityBars } from "../PriorityBars";
import { AnchorChip } from "../AnchorChip";

interface TaskRowProps {
  task: Task;
  columns: BoardColumn[];
  anchorSummary?: AnchorSummary;
  isDragging?: boolean;
  onClick: () => void;
  onStatusChange: (status: string) => void;
  onAnchorClick?: (nodeId: string) => void;
  onDragStart?: (e: React.DragEvent) => void;
  onDragEnd?: () => void;
}

export function TaskRow({
  task,
  columns,
  anchorSummary,
  isDragging,
  onClick,
  onStatusChange,
  onAnchorClick,
  onDragStart,
  onDragEnd,
}: TaskRowProps) {
  const primaryAnchor = task.anchors[0];
  const anchorHot =
    primaryAnchor && anchorSummary?.nodes[primaryAnchor.node_id]?.hot;

  return (
    <tr
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      onClick={onClick}
      className={[
        "group cursor-pointer border-b border-border/50 hover:bg-muted/30",
        isDragging ? "opacity-35" : "",
      ].join(" ")}
    >
      <td className="px-3 py-2 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
        {task.key}
      </td>
      <td className="px-3 py-2 text-sm font-medium max-w-[240px] truncate">
        {task.title}
      </td>
      <td className="px-3 py-2">
        <TaskTypeBadge type={task.task_type} />
      </td>
      <td className="px-3 py-2" onClick={(e) => e.stopPropagation()}>
        <select
          value={task.status}
          onChange={(e) => onStatusChange(e.target.value)}
          className="rounded border border-border bg-background px-1.5 py-0.5 text-xs"
        >
          {columns.map((col) => (
            <option key={col.id} value={col.id}>
              {col.title}
            </option>
          ))}
        </select>
      </td>
      <td className="px-3 py-2">
        <PriorityBars priority={task.priority} />
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap gap-1" onClick={(e) => e.stopPropagation()}>
          {primaryAnchor && (
            <AnchorChip
              anchor={primaryAnchor}
              hot={anchorHot}
              onClick={() => onAnchorClick?.(primaryAnchor.node_id)}
            />
          )}
          {task.blocked && (
            <span className="text-[10px] text-red-400">⊘ blocked</span>
          )}
          {task.subtask_progress.total > 0 && (
            <span className="font-mono text-[10px] text-muted-foreground">
              ✓ {task.subtask_progress.done}/{task.subtask_progress.total}
            </span>
          )}
        </div>
      </td>
    </tr>
  );
}

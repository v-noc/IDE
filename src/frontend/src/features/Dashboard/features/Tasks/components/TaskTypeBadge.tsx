import type { Task, TaskType } from "@/types/tasks";
import { TASK_TYPE_COLORS } from "../theme";

interface TaskTypeBadgeProps {
  type: TaskType;
  className?: string;
}

export function TaskTypeBadge({ type, className = "" }: TaskTypeBadgeProps) {
  const color = TASK_TYPE_COLORS[type];
  return (
    <span
      className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${className}`}
      style={{ color, backgroundColor: `${color}22` }}
    >
      {type}
    </span>
  );
}

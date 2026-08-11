import type { TaskPriority } from "@/types/tasks";
import { PRIORITY_COLORS } from "../theme";

interface PriorityBarsProps {
  priority: TaskPriority;
}

const LEVELS: Record<TaskPriority, number> = {
  none: 0,
  low: 1,
  medium: 2,
  high: 3,
  urgent: 3,
};

export function PriorityBars({ priority }: PriorityBarsProps) {
  const level = LEVELS[priority];
  const color = PRIORITY_COLORS[priority];

  return (
    <span className="inline-flex items-end gap-px h-3" title={priority}>
      {[1, 2, 3].map((bar) => (
        <span
          key={bar}
          className="w-0.5 rounded-sm"
          style={{
            height: `${bar * 3 + 2}px`,
            backgroundColor: bar <= level ? color : "#374151",
            opacity: bar <= level ? 1 : 0.4,
          }}
        />
      ))}
    </span>
  );
}

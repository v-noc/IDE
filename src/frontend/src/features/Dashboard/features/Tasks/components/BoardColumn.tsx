import type { BoardColumn as BoardColumnType, Task, AnchorSummary } from "@/types/tasks";
import { TaskCard } from "./TaskCard";

interface BoardColumnProps {
  column: BoardColumnType;
  tasks: Task[];
  totalInColumn: number;
  anchorSummary?: AnchorSummary;
  draggingTaskId: string | null;
  dropTargetColumnId: string | null;
  onTaskClick: (taskId: string) => void;
  onAnchorClick: (nodeId: string) => void;
  onDragStart: (taskId: string) => void;
  onDragEnd: () => void;
  onDragOver: (e: React.DragEvent, columnId: string) => void;
  onDrop: (e: React.DragEvent, columnId: string) => void;
  onNewTask: (columnId: string) => void;
}

export function BoardColumn({
  column,
  tasks,
  totalInColumn,
  anchorSummary,
  draggingTaskId,
  dropTargetColumnId,
  onTaskClick,
  onAnchorClick,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  onNewTask,
}: BoardColumnProps) {
  const isDropTarget = dropTargetColumnId === column.id;

  return (
    <div className="flex h-full min-w-[240px] flex-1 flex-col">
      <div className="mb-2 flex items-center gap-2 px-1">
        <span
          className="h-2 w-2 rounded-full shrink-0"
          style={{ backgroundColor: column.color }}
        />
        <span className="text-sm font-medium">{column.title}</span>
        <span className="text-xs text-muted-foreground">
          {tasks.length}
          {tasks.length !== totalInColumn && (
            <span className="opacity-60"> of {totalInColumn}</span>
          )}
        </span>
        <button
          type="button"
          onClick={() => onNewTask(column.id)}
          className="ml-auto text-muted-foreground hover:text-foreground text-lg leading-none"
          title="New task in column"
        >
          +
        </button>
      </div>

      <div
        className={[
          "flex flex-1 flex-col gap-2 overflow-y-auto rounded-md p-1 transition-colors",
          isDropTarget
            ? "bg-primary/10 ring-1 ring-primary/40"
            : "bg-muted/20",
        ].join(" ")}
        onDragOver={(e) => onDragOver(e, column.id)}
        onDrop={(e) => onDrop(e, column.id)}
      >
        {tasks.map((task) => (
          <TaskCard
            key={task.id}
            task={task}
            anchorSummary={anchorSummary}
            isDragging={draggingTaskId === task.id}
            onClick={() => onTaskClick(task.id)}
            onAnchorClick={onAnchorClick}
            onDragStart={(e) => {
              e.dataTransfer.effectAllowed = "move";
              onDragStart(task.id);
            }}
            onDragEnd={onDragEnd}
          />
        ))}
      </div>
    </div>
  );
}

import type { AnchorSummary, BoardColumn, Task } from "@/types/tasks";
import { BoardColumn as BoardColumnComponent } from "../BoardColumn";
import { workflowColumns, backlogColumn, countInColumn } from "../../columnUtils";

interface BoardViewProps {
  columns: BoardColumn[];
  allTasks: Task[];
  filteredTasks: Task[];
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
  onBacklogLinkClick: () => void;
}

export function BoardView({
  columns,
  allTasks,
  filteredTasks,
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
  onBacklogLinkClick,
}: BoardViewProps) {
  const workflow = workflowColumns(columns);
  const backlog = backlogColumn(columns);
  const backlogCount = backlog ? countInColumn(allTasks, backlog.id) : 0;

  const tasksByColumn = (columnId: string): Task[] =>
    filteredTasks
      .filter((t) => t.status === columnId)
      .sort((a, b) => a.rank.localeCompare(b.rank));

  const totalByColumn = (columnId: string): number =>
    countInColumn(allTasks, columnId);

  return (
    <div className="flex flex-1 items-stretch gap-3 overflow-x-auto p-4">
      {workflow.map((column) => (
        <BoardColumnComponent
          key={column.id}
          column={column}
          tasks={tasksByColumn(column.id)}
          totalInColumn={totalByColumn(column.id)}
          anchorSummary={anchorSummary}
          draggingTaskId={draggingTaskId}
          dropTargetColumnId={dropTargetColumnId}
          onTaskClick={onTaskClick}
          onAnchorClick={onAnchorClick}
          onDragStart={onDragStart}
          onDragEnd={onDragEnd}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNewTask={onNewTask}
        />
      ))}

      {backlog && backlogCount > 0 && (
        <button
          type="button"
          onClick={onBacklogLinkClick}
          className="self-start mt-1 shrink-0 text-xs text-muted-foreground hover:text-foreground underline-offset-2 hover:underline"
        >
          Backlog {backlogCount}
        </button>
      )}
    </div>
  );
}

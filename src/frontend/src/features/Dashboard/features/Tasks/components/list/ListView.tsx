import { useCallback, useEffectEvent } from "react";
import type { AnchorSummary, BoardColumn, Task } from "@/types/tasks";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { TaskRow } from "./TaskRow";
import { InlineAddRow } from "./InlineAddRow";
import {
  workflowColumns,
  backlogColumn,
  tasksInColumn,
  countInColumn,
  defaultNewTaskColumnId,
} from "../../columnUtils";
import { midRank } from "../../hooks/useBoardDnd";

interface ListViewProps {
  tabId: string;
  columns: BoardColumn[];
  allTasks: Task[];
  filteredTasks: Task[];
  anchorSummary?: AnchorSummary;
  collapsedGroups: string[];
  scrollToBacklog: boolean;
  draggingTaskId: string | null;
  dropTargetColumnId: string | null;
  onToggleGroup: (groupId: string) => void;
  onTaskClick: (taskId: string) => void;
  onAnchorClick: (nodeId: string) => void;
  onMove: (taskId: string, status: string, rank: string) => void;
  onDragStart: (taskId: string) => void;
  onDragEnd: () => void;
  onDragOver: (e: React.DragEvent, columnId: string) => void;
  onDrop: (e: React.DragEvent, columnId: string) => void;
  onAddTask: (columnId: string) => void;
}

export function ListView({
  tabId,
  columns,
  allTasks,
  filteredTasks,
  anchorSummary,
  collapsedGroups,
  scrollToBacklog,
  draggingTaskId,
  dropTargetColumnId,
  onToggleGroup,
  onTaskClick,
  onAnchorClick,
  onMove,
  onDragStart,
  onDragEnd,
  onDragOver,
  onDrop,
  onAddTask,
}: ListViewProps) {
  const clearBacklogScroll = useEffectEvent(() => {
    useProjectStore.getState().clearListBacklogScroll(tabId);
  });

  const backlogRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (!node || !scrollToBacklog) return;
      node.scrollIntoView({ behavior: "smooth", block: "start" });
      clearBacklogScroll();
    },
    [scrollToBacklog, clearBacklogScroll],
  );

  const workflow = workflowColumns(columns);
  const backlog = backlogColumn(columns);
  const activeTasks = filteredTasks.filter(
    (t) => !backlog || t.status !== backlog.id,
  );
  const backlogTasks = backlog
    ? tasksInColumn(
        filteredTasks.filter((t) => t.status === backlog.id),
        backlog.id,
      )
    : [];

  const activeCount = backlog
    ? allTasks.filter((t) => t.status !== backlog.id).length
    : allTasks.length;
  const backlogTotal = backlog ? countInColumn(allTasks, backlog.id) : 0;

  const handleStatusChange = (task: Task, status: string) => {
    const columnTasks = allTasks
      .filter((t) => t.status === status && t.id !== task.id)
      .sort((a, b) => a.rank.localeCompare(b.rank));
    const rank = midRank(
      columnTasks.length > 0 ? columnTasks[columnTasks.length - 1].rank : null,
      null,
    );
    onMove(task.id, status, rank);
  };

  const renderGroup = (column: BoardColumn) => {
    const groupId = column.id;
    const isCollapsed = collapsedGroups.includes(groupId);
    const rows = tasksInColumn(
      activeTasks.filter((t) => t.status === column.id),
      column.id,
    );
    const total = countInColumn(allTasks, column.id);
    if (rows.length === 0 && filteredTasks.length < allTasks.length) return null;

    return (
      <div key={groupId} className="mb-2">
        <button
          type="button"
          onClick={() => onToggleGroup(groupId)}
          onDragOver={(e) => onDragOver(e, column.id)}
          onDrop={(e) => onDrop(e, column.id)}
          className={[
            "flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground hover:bg-muted/20",
            dropTargetColumnId === column.id ? "bg-primary/10 ring-1 ring-primary/40" : "",
          ].join(" ")}
        >
          <span>{isCollapsed ? "▸" : "▾"}</span>
          <span>{column.title}</span>
          <span className="font-normal normal-case">
            ({rows.length}
            {rows.length !== total ? ` of ${total}` : ""})
          </span>
        </button>

        {!isCollapsed && rows.length > 0 && (
          <table className="w-full text-left">
            <tbody>
              {rows.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  columns={columns}
                  anchorSummary={anchorSummary}
                  isDragging={draggingTaskId === task.id}
                  onClick={() => onTaskClick(task.id)}
                  onStatusChange={(status) => handleStatusChange(task, status)}
                  onAnchorClick={onAnchorClick}
                  onDragStart={(e) => {
                    e.dataTransfer.effectAllowed = "move";
                    onDragStart(task.id);
                  }}
                  onDragEnd={onDragEnd}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto px-4 py-3">
      <div className="mb-4">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          ▾ Active ({activeCount})
        </div>
        {workflow.map((column) => renderGroup(column))}
        <InlineAddRow
          label="Add task"
          onClick={() => onAddTask(defaultNewTaskColumnId(columns))}
        />
      </div>

      <div className="my-4 border-t border-border" />

      {backlog && (
        <div ref={backlogRef}>
          <button
            type="button"
            onClick={() => onToggleGroup("backlog")}
            onDragOver={(e) => onDragOver(e, backlog.id)}
            onDrop={(e) => onDrop(e, backlog.id)}
            className={[
              "mb-2 flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:bg-muted/20",
              dropTargetColumnId === backlog.id ? "bg-primary/10 ring-1 ring-primary/40" : "",
            ].join(" ")}
          >
            <span>{collapsedGroups.includes("backlog") ? "▸" : "▾"}</span>
            <span>Backlog</span>
            <span className="font-normal normal-case">
              ({backlogTasks.length}
              {backlogTasks.length !== backlogTotal ? ` of ${backlogTotal}` : ""})
            </span>
          </button>

          {!collapsedGroups.includes("backlog") && (
            <>
              <table className="w-full text-left">
                <tbody>
                  {backlogTasks.map((task) => (
                    <TaskRow
                      key={task.id}
                      task={task}
                      columns={columns}
                      anchorSummary={anchorSummary}
                      isDragging={draggingTaskId === task.id}
                      onClick={() => onTaskClick(task.id)}
                      onStatusChange={(status) => handleStatusChange(task, status)}
                      onAnchorClick={onAnchorClick}
                      onDragStart={(e) => {
                        e.dataTransfer.effectAllowed = "move";
                        onDragStart(task.id);
                      }}
                      onDragEnd={onDragEnd}
                    />
                  ))}
                </tbody>
              </table>
              <InlineAddRow
                label="Add task"
                onClick={() => onAddTask(backlog.id)}
              />
            </>
          )}
        </div>
      )}
    </div>
  );
}

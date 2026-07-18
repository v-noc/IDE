import { useCallback } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { DEFAULT_LIST_COLLAPSED } from "@/features/Dashboard/store/slices/tasksSlice";
import {
  useTaskBoard,
  useAnchorSummary,
  useMoveTask,
} from "./service/useTasks";
import { useTaskFilters } from "./hooks/useTaskFilters";
import { useBoardDnd } from "./hooks/useBoardDnd";
import { FilterBar } from "./components/FilterBar";
import { BoardView } from "./components/board/BoardView";
import { ListView } from "./components/list/ListView";
import { NewTaskModal } from "./components/NewTaskModal";
import { defaultNewTaskColumnId } from "./columnUtils";

interface TasksBoardProps {
  projectId: string;
  tabId: string;
  onNavigateToNode?: (nodeId: string) => void;
}

export function TasksBoard({ projectId, tabId, onNavigateToNode }: TasksBoardProps) {
  const { data: board, isLoading, error } = useTaskBoard(projectId);
  const { data: anchorSummary } = useAnchorSummary(projectId);
  const moveTask = useMoveTask(projectId);

  const taskFilters = useProjectStore((s) => s.taskFilters);
  const setTaskFilters = useProjectStore((s) => s.setTaskFilters);
  const setSelectedTaskId = useProjectStore((s) => s.setSelectedTaskId);
  const openNewTaskModal = useProjectStore((s) => s.openNewTaskModal);
  const taskView = useProjectStore((s) => s.taskView[tabId] ?? "board");
  const setTaskView = useProjectStore((s) => s.setTaskView);
  const listCollapsed = useProjectStore(
    (s) => s.listCollapsed[tabId] ?? DEFAULT_LIST_COLLAPSED,
  );
  const toggleListGroup = useProjectStore((s) => s.toggleListGroup);
  const scrollToBacklog = useProjectStore((s) => s.listScrollToBacklog[tabId] ?? false);
  const requestListBacklogScroll = useProjectStore((s) => s.requestListBacklogScroll);

  const allTasks = board?.tasks ?? [];
  const filteredTasks = useTaskFilters(allTasks, taskFilters);
  const columns = board?.board.columns ?? [];

  const doneColumnIds = new Set(
    columns.filter((c) => c.is_done).map((c) => c.id),
  );
  const openCount = allTasks.filter((t) => !doneColumnIds.has(t.status)).length;

  const handleMove = useCallback(
    (taskId: string, status: string, rank: string) => {
      moveTask.mutate({ taskId, payload: { status, rank } });
    },
    [moveTask],
  );

  const dnd = useBoardDnd({ tasks: allTasks, onMove: handleMove });

  const handleBacklogLinkClick = () => {
    setTaskView(tabId, "list");
    requestListBacklogScroll(tabId);
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground text-sm">
        Loading board…
      </div>
    );
  }

  if (error || !board) {
    return (
      <div className="flex h-full items-center justify-center text-red-400 text-sm">
        Failed to load tasks
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <FilterBar
        view={taskView}
        filters={taskFilters}
        openCount={openCount}
        hotCount={anchorSummary?.hot_count ?? 0}
        onViewChange={(view) => setTaskView(tabId, view)}
        onFiltersChange={setTaskFilters}
        onNewTask={() =>
          openNewTaskModal({ columnId: defaultNewTaskColumnId(columns) })
        }
      />

      {taskView === "board" ? (
        <BoardView
          columns={columns}
          allTasks={allTasks}
          filteredTasks={filteredTasks}
          anchorSummary={anchorSummary}
          draggingTaskId={dnd.draggingTaskId}
          dropTargetColumnId={dnd.dropTargetColumnId}
          onTaskClick={setSelectedTaskId}
          onAnchorClick={(nodeId) => onNavigateToNode?.(nodeId)}
          onDragStart={dnd.handleDragStart}
          onDragEnd={dnd.handleDragEnd}
          onDragOver={dnd.handleDragOver}
          onDrop={dnd.handleDrop}
          onNewTask={(columnId) => openNewTaskModal({ columnId })}
          onBacklogLinkClick={handleBacklogLinkClick}
        />
      ) : (
        <ListView
          tabId={tabId}
          columns={columns}
          allTasks={allTasks}
          filteredTasks={filteredTasks}
          anchorSummary={anchorSummary}
          collapsedGroups={listCollapsed}
          scrollToBacklog={scrollToBacklog}
          draggingTaskId={dnd.draggingTaskId}
          dropTargetColumnId={dnd.dropTargetColumnId}
          onToggleGroup={(groupId) => toggleListGroup(tabId, groupId)}
          onTaskClick={setSelectedTaskId}
          onAnchorClick={(nodeId) => onNavigateToNode?.(nodeId)}
          onMove={handleMove}
          onDragStart={dnd.handleDragStart}
          onDragEnd={dnd.handleDragEnd}
          onDragOver={dnd.handleDragOver}
          onDrop={dnd.handleDrop}
          onAddTask={(columnId) => openNewTaskModal({ columnId })}
        />
      )}

      <NewTaskModal projectId={projectId} />
    </div>
  );
}

export default TasksBoard;

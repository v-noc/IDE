import type { BoardColumn, Task, TaskSubtaskRef } from "@/types/tasks";

export function formatShortDate(iso: string): string {
  const d = new Date(iso);
  return d
    .toLocaleDateString("en-US", { month: "short", day: "numeric" })
    .toLowerCase();
}

export function formatActivityDate(iso: string): string {
  return formatShortDate(iso);
}

export function sortSubtasks(
  subtasks: TaskSubtaskRef[],
  columns: BoardColumn[],
  doneColumnIds: Set<string>,
): TaskSubtaskRef[] {
  const colOrder = new Map(columns.map((c, i) => [c.id, i]));
  return [...subtasks].sort((a, b) => {
    const aDone = doneColumnIds.has(a.status);
    const bDone = doneColumnIds.has(b.status);
    if (aDone !== bDone) return aDone ? 1 : -1;
    const colDiff =
      (colOrder.get(a.status) ?? 99) - (colOrder.get(b.status) ?? 99);
    if (colDiff !== 0) return colDiff;
    return a.key.localeCompare(b.key);
  });
}

export function firstWorkflowColumn(columns: BoardColumn[]): BoardColumn | undefined {
  return columns.find((c) => !c.is_backlog && !c.is_done);
}

export function firstDoneColumn(columns: BoardColumn[]): BoardColumn | undefined {
  return columns.find((c) => c.is_done);
}

export function columnTitle(columns: BoardColumn[], statusId: string): string {
  return columns.find((c) => c.id === statusId)?.title ?? statusId;
}

export function searchLinkableTasks(
  boardTasks: Task[],
  parent: Task,
  query: string,
): Task[] {
  const linked = new Set(parent.subtasks.map((s) => s.id));
  const q = query.trim().toLowerCase();
  return boardTasks.filter((t) => {
    if (t.id === parent.id) return false;
    if (linked.has(t.id)) return false;
    if (!q) return true;
    return (
      t.title.toLowerCase().includes(q) ||
      t.key.toLowerCase().includes(q)
    );
  });
}

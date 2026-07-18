import type { BoardColumn, Task } from "@/types/tasks";

export function isBacklogColumn(column: BoardColumn): boolean {
  return column.is_backlog === true || column.id === "backlog";
}

export function workflowColumns(columns: BoardColumn[]): BoardColumn[] {
  return columns.filter((c) => !isBacklogColumn(c));
}

export function backlogColumn(columns: BoardColumn[]): BoardColumn | undefined {
  return columns.find((c) => isBacklogColumn(c));
}

export function defaultNewTaskColumnId(columns: BoardColumn[]): string {
  const workflow = workflowColumns(columns);
  const todo = workflow.find((c) => c.id === "todo" && !c.is_done);
  if (todo) return todo.id;
  const firstActive = workflow.find((c) => !c.is_done);
  return firstActive?.id ?? workflow[0]?.id ?? columns[0]?.id ?? "todo";
}

export function tasksInColumn(tasks: Task[], columnId: string): Task[] {
  return tasks
    .filter((t) => t.status === columnId)
    .sort((a, b) => a.rank.localeCompare(b.rank));
}

export function countInColumn(tasks: Task[], columnId: string): number {
  return tasks.filter((t) => t.status === columnId).length;
}

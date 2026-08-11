import { useMemo } from "react";
import type { Task, TaskFilters } from "@/types/tasks";

function matchesQuery(task: Task, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;

  if (task.title.toLowerCase().includes(q)) return true;
  if (task.key.toLowerCase().includes(q)) return true;
  if (task.description?.toLowerCase().includes(q)) return true;
  if (task.labels.some((l) => l.toLowerCase().includes(q))) return true;
  if (task.anchors.some((a) => a.qname.toLowerCase().includes(q))) return true;

  return false;
}

export function useTaskFilters(tasks: Task[], filters: TaskFilters): Task[] {
  return useMemo(() => {
    return tasks.filter((task) => {
      if (filters.type !== "all" && task.task_type !== filters.type) {
        return false;
      }
      if (filters.priority !== "all" && task.priority !== filters.priority) {
        return false;
      }
      if (filters.label && !task.labels.includes(filters.label)) {
        return false;
      }
      if (!matchesQuery(task, filters.query)) {
        return false;
      }
      return true;
    });
  }, [tasks, filters]);
}

export interface TaskSubWire {
  id?: string;
  title?: string;
  /** Backend `SubTask` wire uses `name`. */
  name?: string;
  description?: string;
  state?: string;
}

export interface TaskWirePart {
  type: "task";
  task_id: string;
  title: string;
  description?: string;
  state: string;
  progress?: number;
  workflow_name?: string;
  /** Optional Lucide icon name (e.g. "sparkles", "cpu"). */
  icon?: string;
  sub_tasks?: TaskSubWire[];
  /** Hint when sub-tasks exist in DB but are not embedded in the part. */
  sub_task_count?: number;
}

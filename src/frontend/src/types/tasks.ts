export type TaskType = "epic" | "task" | "bug" | "improvement";
export type TaskPriority = "none" | "low" | "medium" | "high" | "urgent";

export interface TaskAnchor {
  node_id: string;
  qname: string;
  kind: string;
  is_resolved?: boolean;
}

export interface TaskSubtaskRef {
  id: string;
  key: string;
  title: string;
  status: string;
  shared?: boolean;
}

export interface TaskRef {
  id: string;
  key: string;
  title: string;
  status: string;
}

export interface TaskNote {
  text: string;
  at: string;
  origin: "system" | "user";
}

export interface SubtaskProgress {
  done: number;
  total: number;
}

export interface Task {
  id: string;
  key: string;
  title: string;
  description: string;
  task_type: TaskType;
  status: string;
  priority: TaskPriority;
  labels: string[];
  rank: string;
  anchors: TaskAnchor[];
  subtasks: TaskSubtaskRef[];
  blocked_by: TaskRef[];
  blocks: string[];
  notes: TaskNote[];
  blocked: boolean;
  subtask_progress: SubtaskProgress;
  created_at: string;
  updated_at: string;
}

export interface BoardColumn {
  id: string;
  title: string;
  color: string;
  is_done: boolean;
  is_backlog?: boolean;
}

export type TaskView = "board" | "list";

export interface BoardPayload {
  board: {
    id: string;
    columns: BoardColumn[];
    task_counter: number;
  };
  tasks: Task[];
}

export interface AnchorSummaryNode {
  qname: string;
  open_task_ids: string[];
  open_count: number;
  hot: boolean;
}

export interface AnchorSummary {
  nodes: Record<string, AnchorSummaryNode>;
  hot_count: number;
}

export interface DependencySuggestion {
  node_id: string;
  qname: string;
  kind: string;
}

export interface ReAnchorCandidate {
  node_id: string;
  qname: string;
  kind: string;
}

export interface TaskFilters {
  query: string;
  type: TaskType | "all";
  label: string;
  priority: TaskPriority | "all";
}

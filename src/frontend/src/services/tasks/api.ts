import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import { toProjectApiId } from "@/lib/projectId";
import type {
  AnchorSummary,
  BoardPayload,
  DependencySuggestion,
  ReAnchorCandidate,
  Task,
  TaskType,
  TaskPriority,
} from "@/types/tasks";

function buildQueryString(params: Record<string, string>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v != null && v !== "") search.set(k, v);
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

function projectQs(projectId: string, extra: Record<string, string> = {}): string {
  return buildQueryString({ project_id: toProjectApiId(projectId), ...extra });
}

export interface CreateTaskPayload {
  title: string;
  task_type?: TaskType;
  priority?: TaskPriority;
  description?: string;
  labels?: string[];
  status?: string;
  anchors?: { node_id: string }[];
  subtask_of?: string;
}

export interface UpdateTaskPayload {
  title?: string;
  description?: string;
  task_type?: TaskType;
  priority?: TaskPriority;
  labels?: string[];
}

export interface MoveTaskPayload {
  status: string;
  rank: string;
}

export const tasksApi = {
  getBoard: async (projectId: string): Promise<BoardPayload> => {
    return api(`${API_ROUTES.TASKS}/board${projectQs(projectId)}`);
  },

  getAnchorSummary: async (projectId: string): Promise<AnchorSummary> => {
    return api(`${API_ROUTES.TASKS}/anchor-summary${projectQs(projectId)}`);
  },

  createTask: async (
    projectId: string,
    payload: CreateTaskPayload,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}${projectQs(projectId)}`, { method: "POST", body: payload });
  },

  updateTask: async (
    projectId: string,
    taskId: string,
    payload: UpdateTaskPayload,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/${projectQs(projectId, { task_id: taskId })}`, {
      method: "PATCH",
      body: payload,
    });
  },

  moveTask: async (
    projectId: string,
    taskId: string,
    payload: MoveTaskPayload,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/move${projectQs(projectId, { task_id: taskId })}`, {
      method: "POST",
      body: payload,
    });
  },

  deleteTask: async (projectId: string, taskId: string): Promise<void> => {
    await api(`${API_ROUTES.TASKS}/${projectQs(projectId, { task_id: taskId })}`, {
      method: "DELETE",
    });
  },

  addSubtask: async (
    projectId: string,
    parentId: string,
    payload: { child_id?: string; title?: string; anchors?: { node_id: string }[] },
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/subtasks${projectQs(projectId, { task_id: parentId })}`, {
      method: "POST",
      body: payload,
    });
  },

  removeSubtask: async (
    projectId: string,
    parentId: string,
    childId: string,
  ): Promise<void> => {
    await api(
      `${API_ROUTES.TASKS}/subtasks${projectQs(projectId, { task_id: parentId, child_id: childId })}`,
      { method: "DELETE" },
    );
  },

  addBlockedBy: async (
    projectId: string,
    taskId: string,
    blockerId: string,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/blocked-by${projectQs(projectId, { task_id: taskId })}`, {
      method: "POST",
      body: { blocker_id: blockerId },
    });
  },

  addAnchor: async (
    projectId: string,
    taskId: string,
    nodeId: string,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/anchors${projectQs(projectId, { task_id: taskId })}`, {
      method: "POST",
      body: { node_id: nodeId },
    });
  },

  removeAnchor: async (
    projectId: string,
    taskId: string,
    nodeId: string,
  ): Promise<void> => {
    await api(
      `${API_ROUTES.TASKS}/anchors${projectQs(projectId, { task_id: taskId, node_id: nodeId })}`,
      { method: "DELETE" },
    );
  },

  moveAnchor: async (
    projectId: string,
    taskId: string,
    fromNodeId: string,
    toNodeId: string,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/anchors/move${projectQs(projectId, { task_id: taskId })}`, {
      method: "POST",
      body: { from_node_id: fromNodeId, to_node_id: toNodeId },
    });
  },

  addNote: async (
    projectId: string,
    taskId: string,
    text: string,
  ): Promise<Task> => {
    return api(`${API_ROUTES.TASKS}/notes${projectQs(projectId, { task_id: taskId })}`, {
      method: "POST",
      body: { text },
    });
  },

  suggestDependencies: async (
    projectId: string,
    nodeId: string,
  ): Promise<DependencySuggestion[]> => {
    return api(
      `${API_ROUTES.TASKS}/suggest-dependencies${projectQs(projectId, { node_id: nodeId })}`,
    );
  },

  reAnchorCandidates: async (
    projectId: string,
    qname: string,
    kind?: string,
  ): Promise<ReAnchorCandidate[]> => {
    const extra: Record<string, string> = { qname };
    if (kind) extra.kind = kind;
    return api(`${API_ROUTES.TASKS}/re-anchor-candidates${projectQs(projectId, extra)}`);
  },
};

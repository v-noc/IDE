import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface LogNode {
  _id: string;
  _key: string;
  timestamp: string;
  event_type: "enter" | "exit" | "error" | "log";
  message: string;
  level_name: string | null;
  duration_ms: number | null;
  chain_id: string | null;
  payload: { [key: string]: unknown } | null;
  result: unknown | null;
  error: { [key: string]: unknown } | null;
  created_at: string;
  function_id: string | null;
}

export interface LogTreeNode extends LogNode {
  children: LogTreeNode[];
}

export const logsApi = {
  getLogTree: (functionId: string, projectId: string): Promise<LogTreeNode[]> =>
    api(`${API_ROUTES.LOGS}/log-tree?function_id=${functionId}&project_id=${projectId}`),
};

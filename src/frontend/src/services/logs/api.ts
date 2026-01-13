import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface LogNode {
  _id: string;
  created_at: string;
  timestamp: string;
  event_type: string;
  message: string;
  duration_ms: number | null;
  chain_id: string | null;
  payload: Record<string, unknown> | null;
  result: unknown | null;
  error: Record<string, unknown> | null;
  level_name: string | null;
}


export interface LogTreeNode extends LogNode {
  children: LogTreeNode[];
}

export const logsApi = {
  getLogTree: (nodeId: string): Promise<LogTreeNode[]> =>
    api(`${API_ROUTES.LOGS}${nodeId}/tree`),
};

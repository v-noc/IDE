import { agentFetch } from "@/lib/agentFetch";
import { AGENT_ROUTES } from "@/lib/agentRoutes";
import type {
  RunWorkflowBatchRequest,
  RunWorkflowBatchResponse,
  RunWorkflowRequest,
  RunWorkflowResponse,
} from "@/types/agent/workflows";

export const agentWorkflowsApi = {
  run: (projectId: string, body: RunWorkflowRequest) =>
    agentFetch<RunWorkflowResponse>(
      AGENT_ROUTES.WORKFLOWS_RUN,
      { method: "POST", body },
      projectId,
    ),

  runBatch: (projectId: string, body: RunWorkflowBatchRequest) =>
    agentFetch<RunWorkflowBatchResponse>(
      AGENT_ROUTES.WORKFLOWS_RUN_BATCH,
      { method: "POST", body },
      projectId,
    ),
};

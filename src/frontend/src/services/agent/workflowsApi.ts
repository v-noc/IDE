import { agentFetch } from "@/lib/agentFetch";
import { AGENT_ROUTES } from "@/lib/agentRoutes";
import type { RunWorkflowRequest, RunWorkflowResponse } from "@/types/agent/workflows";

export const agentWorkflowsApi = {
  run: (projectId: string, body: RunWorkflowRequest) =>
    agentFetch<RunWorkflowResponse>(
      AGENT_ROUTES.WORKFLOWS_RUN,
      { method: "POST", body },
      projectId,
    ),
};

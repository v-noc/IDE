/** Agent HTTP paths (mounted under `VITE_API_BASE_URL`, default `/api/v1`). */
export const AGENT_ROUTES = {
  WORKFLOWS_RUN: "/agent/workflows/run",
  WORKFLOWS_RUN_BATCH: "/agent/workflows/run-batch",
} as const;

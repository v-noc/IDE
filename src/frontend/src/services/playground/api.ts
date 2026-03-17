import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type {
  CreatePlaygroundPayload,
  Playground,
  RunPlaygroundCodePayload,
  RunPlaygroundCodeResponse,
  UpdatePlaygroundPayload,
} from "@/types/playground";

function withProjectId(path: string, projectId: string): string {
  const params = new URLSearchParams({ project_id: projectId });
  return `${path}?${params.toString()}`;
}

function withProjectAndNodeId(
  path: string,
  projectId: string,
  nodeId: string
): string {
  const params = new URLSearchParams({ project_id: projectId, node_id: nodeId });
  return `${path}?${params.toString()}`;
}

export const playgroundApi = {
  create: (
    payload: CreatePlaygroundPayload,
    projectId: string
  ): Promise<Playground> =>
    api(withProjectId(`${API_ROUTES.PLAYGROUNDS}/`, projectId), {
      method: "POST",
      body: payload,
    }),

  getById: (playgroundId: string, projectId: string): Promise<Playground> =>
    api(withProjectId(`${API_ROUTES.PLAYGROUNDS}/${playgroundId}`, projectId)),

  update: (
    playgroundId: string,
    payload: UpdatePlaygroundPayload,
    projectId: string
  ): Promise<Playground> =>
    api(withProjectId(`${API_ROUTES.PLAYGROUNDS}/${playgroundId}`, projectId), {
      method: "PUT",
      body: payload,
    }),

  delete: (playgroundId: string, projectId: string): Promise<void> =>
    api(withProjectId(`${API_ROUTES.PLAYGROUNDS}/${playgroundId}`, projectId), {
      method: "DELETE",
    }),

  getByOwnerNodeId: (nodeId: string, projectId: string): Promise<Playground[]> =>
    api(withProjectAndNodeId(`${API_ROUTES.PLAYGROUNDS}/owners`, projectId, nodeId)),

  runCode: (
    payload: RunPlaygroundCodePayload,
    projectId: string
  ): Promise<RunPlaygroundCodeResponse> =>
    api(withProjectId(`${API_ROUTES.PLAYGROUNDS}/run-code`, projectId), {
      method: "POST",
      body: payload,
    }),
};

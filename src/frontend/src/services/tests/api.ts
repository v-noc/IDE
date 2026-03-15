import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface TestConfigResponse {
  id: string;
  enabled: boolean;
  test_root: string;
  test_args: string;
}

export interface CreateTestConfigPayload {
  enabled: boolean;
  test_root: string;
  test_args: string;
}

export interface UpdateTestConfigPayload {
  enabled?: boolean;
  test_root?: string;
  test_args?: string;
}

export interface RunTestsPayload {
  node_id?: string;
  owner_id?: string;
}

export interface RunResultResponse {
  exit_code: number;
  test_cases: number;
  test_links: number;
  persisted: boolean;
}

export interface RunTestsResponse {
  mode: string;
  run?: RunResultResponse | null;
  runs: RunResultResponse[];
  total_runs: number;
  total_test_cases: number;
  total_test_links: number;
}

function withProjectId(path: string, projectId: string): string {
  const query = new URLSearchParams({ project_id: projectId });
  return `${path}?${query.toString()}`;
}

export const testsApi = {
  getConfig: (projectId: string): Promise<TestConfigResponse> =>
    api(withProjectId(`${API_ROUTES.TESTS}/config`, projectId)),

  createConfig: (
    payload: CreateTestConfigPayload,
    projectId: string,
  ): Promise<TestConfigResponse> =>
    api(withProjectId(`${API_ROUTES.TESTS}/config`, projectId), {
      method: "POST",
      body: payload,
    }),

  updateConfig: (
    payload: UpdateTestConfigPayload,
    projectId: string,
  ): Promise<TestConfigResponse> =>
    api(withProjectId(`${API_ROUTES.TESTS}/config`, projectId), {
      method: "PUT",
      body: payload,
    }),

  runTests: (
    payload: RunTestsPayload,
    projectId: string,
  ): Promise<RunTestsResponse> =>
    api(withProjectId(`${API_ROUTES.TESTS}/run`, projectId), {
      method: "POST",
      body: payload,
    }),
};

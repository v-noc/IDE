import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface TestConfigResponse {
  id: string;
  enabled: boolean;
  test_root: string;
  test_args: string;
  executable_path?: string | null;
}

export interface CreateTestConfigPayload {
  enabled: boolean;
  test_root: string;
  test_args: string;
  executable_path?: string | null;
}

export interface UpdateTestConfigPayload {
  enabled?: boolean;
  test_root?: string;
  test_args?: string;
  executable_path?: string | null;
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
  error_message?: string | null;
  raw_output?: string | null;
}

export interface RunTestsResponse {
  mode: string;
  run?: RunResultResponse | null;
  runs: RunResultResponse[];
  total_runs: number;
  total_test_cases: number;
  total_test_links: number;
}

export interface TestCaseResponse {
  "@id"?: string;
  id?: string;
  name: string;
  description?: string;
  node_id: string;
  path: string;
  target_function?:
    | string
    | {
        "@id"?: string;
        id?: string;
        name?: string;
        description?: string;
      }
    | null;
  test_links?: unknown[];
}

export interface TestCasesResponse {
  test_cases: TestCaseResponse[];
  lines: number[];
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

  getTestCases: (nodeId: string, projectId: string): Promise<TestCasesResponse> => {
    const params = new URLSearchParams({ project_id: projectId, node_id: nodeId });
    return api(`${API_ROUTES.TESTS}/cases?${params.toString()}`);
  },
};

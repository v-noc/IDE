import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { testsApi, type TestCasesResponse, type TestConfigResponse } from "./api";

export const useTestConfig = (projectId: string) => {
  return useQuery<TestConfigResponse>({
    queryKey: queryKeys.tests.config(projectId),
    queryFn: () => testsApi.getConfig(projectId),
    enabled: !!projectId,
    retry: false,
  });
};

export const useTestCases = (nodeId: string | null, projectId: string) => {
  return useQuery<TestCasesResponse>({
    queryKey: queryKeys.tests.cases(projectId, nodeId ?? ""),
    queryFn: () => testsApi.getTestCases(nodeId!, projectId),
    enabled: !!nodeId && !!projectId,
    retry: false,
  });
};

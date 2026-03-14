import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { testsApi, type TestConfigResponse } from "./api";

export const useTestConfig = (projectId: string) => {
  return useQuery<TestConfigResponse>({
    queryKey: queryKeys.tests.config(projectId),
    queryFn: () => testsApi.getConfig(projectId),
    enabled: !!projectId,
    retry: false,
  });
};

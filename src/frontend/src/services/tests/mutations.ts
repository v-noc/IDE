import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import {
  testsApi,
  type CreateTestConfigPayload,
  type UpdateTestConfigPayload,
} from "./api";

export const useCreateTestConfig = (projectId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateTestConfigPayload) =>
      testsApi.createConfig(payload, projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.config(projectId) });
    },
  });
};

export const useUpdateTestConfig = (projectId: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateTestConfigPayload) =>
      testsApi.updateConfig(payload, projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tests.config(projectId) });
    },
  });
};

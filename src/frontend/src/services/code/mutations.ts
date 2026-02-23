import { useMutation, useQueryClient } from "@tanstack/react-query";
import { codeApi } from "./api";
import queryKeys from "@/lib/queryKeys";

/**
 * Write code mutation.
 * Automatically invalidates the cache so all consumers update.
 */
export const useWriteCode = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ elementId, code, projectId }: { elementId: string; code: string; projectId: string }) =>
      codeApi.writeCode(elementId, code, projectId),
    onSuccess: (_, { elementId, projectId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.code.detail(elementId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.tree(projectId) });
    },
  });
}

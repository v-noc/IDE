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
    mutationFn: ({ elementId, code }: { elementId: string; code: string }) => codeApi.writeCode(elementId, code),
    onSuccess: (_, { elementId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.code.detail(elementId) });
    },
  });
}

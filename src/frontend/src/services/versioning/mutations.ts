import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { versioningApi } from "./api";

export const useCreateBranch = (projectId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => versioningApi.createBranch(projectId, name),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.versioning.branches(projectId),
      });
    },
  });
};

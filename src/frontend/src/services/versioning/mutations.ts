import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { versioningApi } from "./api";

export const useCreateBranch = (projectId: string | undefined) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => {
      if (!projectId) {
        throw new Error("Project id is required to create a branch");
      }
      return versioningApi.createBranch(projectId, name);
    },
    onSuccess: () => {
      if (!projectId) return;
      queryClient.invalidateQueries({
        queryKey: queryKeys.versioning.branches(projectId),
      });
    },
  });
};

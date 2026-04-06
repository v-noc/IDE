import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { versioningApi, type VersioningRemoteAuth } from "./api";

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

export const usePushToRemote = (
  projectId: string | undefined,
  branch: string | undefined
) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (remote_auth: VersioningRemoteAuth) => {
      if (!projectId) {
        throw new Error("Project id is required to push");
      }
      return versioningApi.push(
        projectId,
        { remote: "origin", remote_auth },
        { branch }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.versioning.all });
    },
  });
};

export const usePullFromRemote = (
  projectId: string | undefined,
  branch: string | undefined
) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (remote_auth: VersioningRemoteAuth) => {
      if (!projectId) {
        throw new Error("Project id is required to pull");
      }
      return versioningApi.pull(
        projectId,
        { remote: "origin", remote_auth },
        { branch }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.versioning.all });
    },
  });
};

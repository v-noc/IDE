import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { versioningApi, type Commit, type Branch } from "./api";

export const useBranches = (projectId: string | undefined) => {
  return useQuery<Branch[]>({
    queryKey: queryKeys.versioning.branches(projectId ?? ""),
    queryFn: () => versioningApi.getBranches(projectId!),
    enabled: !!projectId,
  });
};

export const useCommits = (
  projectId: string | undefined,
  nodeId: string | undefined,
  options?: { start?: number; count?: number }
) => {
  return useQuery<Commit[]>({
    queryKey: queryKeys.versioning.commits(
      projectId ?? "",
      nodeId ?? "",
      options?.start,
      options?.count
    ),
    queryFn: () =>
      versioningApi.getCommits(projectId!, nodeId!, {
        start: options?.start,
        count: options?.count,
      }),
    enabled: !!projectId && !!nodeId,
  });
};

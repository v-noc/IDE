import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { versioningApi, type Commit, type Branch, type TerminusJsonDiff } from "./api";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

export const useBranches = (
  projectId: string | undefined,
  options?: { branch?: string; ref?: string }
) => {
  const branchFromStore = useVersioningStore((s) => s.branch);
  const refFromStore = useVersioningStore((s) => s.checkedOutCommitId);
  const branch = options?.branch ?? branchFromStore;
  const ref = options?.ref ?? refFromStore ?? undefined;

  return useQuery<Branch[]>({
    queryKey: queryKeys.versioning.branches(projectId ?? "", branch, ref),
    queryFn: () => versioningApi.getBranches(projectId!, options),
    enabled: !!projectId,
  });
};

export const useCommits = (
  projectId: string | undefined,
  nodeId: string | undefined,
  options?: {
    start?: number;
    count?: number;
    enabled?: boolean;
    branch?: string;
    ref?: string;
  }
) => {
  const branchFromStore = useVersioningStore((s) => s.branch);
  const refFromStore = useVersioningStore((s) => s.checkedOutCommitId);
  const branch = options?.branch ?? branchFromStore;
  const ref = options?.ref ?? refFromStore ?? undefined;

  return useQuery<Commit[]>({
    queryKey: queryKeys.versioning.commits(
      projectId ?? "",
      nodeId ?? "",
      options?.start,
      options?.count,
      branch,
      ref
    ),
    queryFn: () =>
      versioningApi.getCommits(projectId!, nodeId!, {
        start: options?.start,
        count: options?.count,
        branch: options?.branch,
        ref: options?.ref,
      }),
    enabled: (options?.enabled ?? true) && !!projectId && !!nodeId,
  });
};

export const useSuspenseCommits = (
  projectId: string,
  nodeId: string,
  options?: { start?: number; count?: number; branch?: string; ref?: string }
) => {
  const branchFromStore = useVersioningStore((s) => s.branch);
  const refFromStore = useVersioningStore((s) => s.checkedOutCommitId);
  const branch = options?.branch ?? branchFromStore;
  const ref = options?.ref ?? refFromStore ?? undefined;

  return useSuspenseQuery<Commit[]>({
    queryKey: queryKeys.versioning.commits(
      projectId,
      nodeId,
      options?.start,
      options?.count,
      branch,
      ref
    ),
    queryFn: () =>
      versioningApi.getCommits(projectId, nodeId, {
        start: options?.start,
        count: options?.count,
        branch: options?.branch,
        ref: options?.ref,
      }),
  });
};

export const useCommitDiff = (
  projectId: string | undefined,
  afterCommitId: string | null,
  beforeCommitId: string | null,
  options?: { branch?: string; ref?: string }
) => {
  const branchFromStore = useVersioningStore((s) => s.branch);
  const refFromStore = useVersioningStore((s) => s.checkedOutCommitId);
  const branch = options?.branch ?? branchFromStore;
  const ref = options?.ref ?? refFromStore ?? undefined;

  return useQuery<TerminusJsonDiff>({
    queryKey: queryKeys.versioning.diff(
      projectId ?? "",
      afterCommitId ?? "",
      beforeCommitId ?? "",
      branch,
      ref
    ),
    queryFn: () =>
      versioningApi.getDiff(projectId!, afterCommitId!, beforeCommitId!, options),
    enabled:
      !!projectId &&
      !!afterCommitId &&
      !!beforeCommitId &&
      afterCommitId !== beforeCommitId,
  });
};

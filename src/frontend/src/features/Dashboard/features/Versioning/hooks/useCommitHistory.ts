import { useCommitDiff, useCommits } from "@/services/versioning";

export type { Commit, TerminusJsonDiff } from "@/services/versioning";

export function useCommitHistory(
  projectId: string | undefined,
  nodeId: string | undefined,
  options?: {
    start?: number;
    count?: number;
    enabled?: boolean;
    branch?: string;
    ref?: string;
  }
) {
  return useCommits(projectId, nodeId, options);
}

export function useSelectedCommitDiff(
  projectId: string | undefined,
  targetCommitId: string | null,
  compareToCommitId: string | null,
  options?: { branch?: string; ref?: string }
) {
  return useCommitDiff(projectId, targetCommitId, compareToCommitId, options);
}

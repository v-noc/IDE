import { useCommitDiff, useCommits } from "@/services/versioning";

export type { Commit, TerminusJsonDiff } from "@/services/versioning";

export function useCommitHistory(
  projectId: string | undefined,
  nodeId: string | undefined,
  options?: { start?: number; count?: number }
) {
  return useCommits(projectId, nodeId, options);
}

export function useSelectedCommitDiff(
  projectId: string | undefined,
  selectedCommitId: string | null,
  currentCommitId: string | null
) {
  return useCommitDiff(projectId, selectedCommitId, currentCommitId);
}

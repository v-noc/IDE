import { useCommits } from "@/services/versioning";

export type { Commit } from "@/services/versioning";

export function useCommitHistory(
  projectId: string | undefined,
  nodeId: string | undefined,
  options?: { start?: number; count?: number }
) {
  return useCommits(projectId, nodeId, options);
}

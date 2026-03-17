import { useMemo } from "react";
import { useBranches, useCreateBranch } from "@/services/versioning";
import { useVersioningStore } from "../store/useVersioningStore";
import {
  versioningBranchService,
  type VersioningBranch,
} from "../services/versioningBranchService";

function compareBranches(a: VersioningBranch, b: VersioningBranch): number {
  if (a.isCurrent && !b.isCurrent) return -1;
  if (!a.isCurrent && b.isCurrent) return 1;
  return a.name.localeCompare(b.name);
}

export function useVersioningBranches(projectId: string | undefined) {
  const currentBranch = useVersioningStore((s) => s.branch);
  const setBranch = useVersioningStore((s) => s.setBranch);
  const setCheckedOutCommitId = useVersioningStore((s) => s.setCheckedOutCommitId);
  const clearComparisonState = useVersioningStore((s) => s.clearComparisonState);

  const branchesQuery = useBranches(projectId);
  const createBranchMutation = useCreateBranch(projectId);

  const availableBranches = useMemo(() => {
    const byName = new Map<string, VersioningBranch>();

    for (const branch of branchesQuery.data ?? []) {
      const normalized = versioningBranchService.normalizeBranch(branch);
      byName.set(normalized.name, normalized);
    }

    if (!byName.has(currentBranch)) {
      byName.set(currentBranch, {
        id: currentBranch,
        name: currentBranch,
        isCurrent: true,
        headCommit: "",
      });
    }

    return [...byName.values()].sort(compareBranches);
  }, [branchesQuery.data, currentBranch]);

  const switchBranch = (nextBranch: string) => {
    if (!nextBranch || nextBranch === currentBranch) return;
    setBranch(nextBranch);
    setCheckedOutCommitId(null);
    clearComparisonState();
  };

  const createBranch = async (name: string) => {
    const trimmed = name.trim();
    if (!trimmed) return;
    await createBranchMutation.mutateAsync(trimmed);
    switchBranch(trimmed);
  };

  return {
    currentBranch,
    availableBranches,
    switchBranch,
    createBranch,
    isLoadingBranches: branchesQuery.isLoading,
    isCreatingBranch: createBranchMutation.isPending,
  };
}

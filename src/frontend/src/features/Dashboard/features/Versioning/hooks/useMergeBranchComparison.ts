import { useCallback, useEffect, useMemo } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useVersioningBranches } from "./useVersioningBranches";
import { useVersioningStore } from "../store/useVersioningStore";

export function useMergeBranchComparison() {
  const currentBranch = useVersioningStore((s) => s.branch);
  const isMergeMode = useVersioningStore((s) => s.isMergeMode);
  const mergeSourceBranch = useVersioningStore((s) => s.mergeSourceBranch);
  const mergeTargetBranch = useVersioningStore((s) => s.mergeTargetBranch);
  const setMergeSourceBranch = useVersioningStore((s) => s.setMergeSourceBranch);
  const setMergeTargetBranch = useVersioningStore((s) => s.setMergeTargetBranch);
  const setCheckedOutCommitId = useVersioningStore((s) => s.setCheckedOutCommitId);
  const setCompareToCommitId = useVersioningStore((s) => s.setCompareToCommitId);

  const projectId = useProjectStore((s) => s.projectData?.id);
  const { availableBranches, isLoadingBranches } = useVersioningBranches(projectId);

  const sourceBranch = mergeSourceBranch ?? currentBranch;
  const branchByName = useMemo(
    () => new Map(availableBranches.map((branch) => [branch.name, branch])),
    [availableBranches],
  );

  const mergeCandidates = useMemo(
    () => availableBranches.filter((candidate) => candidate.name !== sourceBranch),
    [availableBranches, sourceBranch],
  );

  const resolvedTargetBranch = useMemo(() => {
    if (!mergeTargetBranch) return mergeCandidates[0]?.name ?? null;
    const exists = mergeCandidates.some((candidate) => candidate.name === mergeTargetBranch);
    return exists ? mergeTargetBranch : (mergeCandidates[0]?.name ?? null);
  }, [mergeCandidates, mergeTargetBranch]);

  useEffect(() => {
    if (!isMergeMode) return;
    if (mergeSourceBranch !== sourceBranch) {
      setMergeSourceBranch(sourceBranch);
    }
    if (mergeTargetBranch !== resolvedTargetBranch) {
      setMergeTargetBranch(resolvedTargetBranch);
    }
  }, [
    isMergeMode,
    mergeSourceBranch,
    sourceBranch,
    mergeTargetBranch,
    resolvedTargetBranch
  ]);

  useEffect(() => {
    if (!isMergeMode) return;
    const sourceHead = branchByName.get(sourceBranch)?.headCommit ?? null;
    const targetHead =
      resolvedTargetBranch != null
        ? (branchByName.get(resolvedTargetBranch)?.headCommit ?? null)
        : null;
    setCheckedOutCommitId(sourceBranch === currentBranch ? null : sourceHead);
    setCompareToCommitId(targetHead);
  }, [
    isMergeMode,
    sourceBranch,
    resolvedTargetBranch,
    currentBranch,
    branchByName

  ]);

  const swapMergeBranches = useCallback(() => {
    if (!resolvedTargetBranch) return;
    setMergeSourceBranch(resolvedTargetBranch);
    setMergeTargetBranch(sourceBranch);
  }, [resolvedTargetBranch, sourceBranch, setMergeSourceBranch, setMergeTargetBranch]);

  const selectMergeTargetBranch = useCallback(
    (nextBranch: string) => {
      if (!nextBranch || nextBranch === sourceBranch) return;
      setMergeTargetBranch(nextBranch);
    },
    [sourceBranch, setMergeTargetBranch],
  );

  return {
    isMergeMode,
    isLoadingBranches,
    sourceBranch,
    mergeCandidates,
    targetBranch: resolvedTargetBranch,
    selectMergeTargetBranch,
    swapMergeBranches,
  };
}

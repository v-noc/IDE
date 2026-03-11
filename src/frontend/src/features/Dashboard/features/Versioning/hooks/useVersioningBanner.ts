import { useCallback } from "react";
import { useVersioningStore } from "../store/useVersioningStore";

function shortCommit(id: string | null): string {
  if (!id) return "";

  return id.slice(0, 8);
}

export function useVersioningBanner() {
  const branch = useVersioningStore((s) => s.branch);
  const headCommitId = useVersioningStore((s) => s.headCommitId);
  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);

  const setCheckedOutCommitId = useVersioningStore((s) => s.setCheckedOutCommitId);
  const setCompareToCommitId = useVersioningStore((s) => s.setCompareToCommitId);
  const clearComparisonState = useVersioningStore(
    (s) => s.clearComparisonState,
  );

  const targetCommitId = checkedOutCommitId ?? headCommitId;
  const isVisible = Boolean(checkedOutCommitId || compareToCommitId);
  const isComparing = Boolean(compareToCommitId && targetCommitId);

  const swapCompare = useCallback(() => {
    if (!compareToCommitId || !targetCommitId || compareToCommitId === targetCommitId) return;
    setCompareToCommitId(targetCommitId);
    setCheckedOutCommitId(compareToCommitId);
  }, [compareToCommitId, targetCommitId, setCompareToCommitId, setCheckedOutCommitId]);

  const clearCompare = useCallback(() => {

    clearComparisonState();
  }, [compareToCommitId]);

  const closeBanner = useCallback(() => {
    setCheckedOutCommitId(null);
    clearComparisonState();
  }, [setCheckedOutCommitId, clearComparisonState]);

  return {
    branch,
    headCommitId,
    checkedOutCommitId,
    compareToCommitId,
    targetCommitId,
    isVisible,
    isComparing,
    shortCommit,
    swapCompare,
    clearCompare,
    closeBanner,
  };
}

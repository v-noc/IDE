import { useCallback } from "react";
import { useVersioningStore } from "../store/useVersioningStore";

function shortCommit(id: string | null): string {
  if (!id) return "";
  if (id.startsWith("branch:")) return id.slice("branch:".length);

  return id.slice(0, 8);
}

export function useVersioningBanner() {
  const branch = useVersioningStore((s) => s.branch);
  const headCommitId = useVersioningStore((s) => s.headCommitId);
  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);
  const showAffectedOnly = useVersioningStore((s) => s.showAffectedOnly);

  const setCheckedOutCommitId = useVersioningStore((s) => s.setCheckedOutCommitId);
  const setCompareToCommitId = useVersioningStore((s) => s.setCompareToCommitId);
  const clearComparisonState = useVersioningStore(
    (s) => s.clearComparisonState,
  );
  const setShowAffectedOnly = useVersioningStore((s) => s.setShowAffectedOnly);

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
  }, [clearComparisonState]);

  const closeBanner = useCallback(() => {
    setCheckedOutCommitId(null);
    clearComparisonState();
  }, [setCheckedOutCommitId, clearComparisonState]);

  return {
    branch,
    headCommitId,
    checkedOutCommitId,
    compareToCommitId,
    showAffectedOnly,
    targetCommitId,
    isVisible,
    isComparing,
    shortCommit,
    swapCompare,
    clearCompare,
    closeBanner,
    setShowAffectedOnly,
  };
}

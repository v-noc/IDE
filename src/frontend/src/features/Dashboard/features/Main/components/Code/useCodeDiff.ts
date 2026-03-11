import { useMemo } from "react";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import type { CodeData } from "@/services/code";

export interface UseCodeDiffResult {
  showDiff: boolean;
  originalContent: string;
  modifiedContent: string;
  isLoadingDiff: boolean;
  error: string | null;
}

interface UseCodeDiffParams {
  codeData?: CodeData;
}

export function useCodeDiff({
  codeData,
}: UseCodeDiffParams): UseCodeDiffResult {
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);

  return useMemo(() => {
    const showDiff = Boolean(compareToCommitId && codeData?.compare_to);
    if (!showDiff) {
      return {
        showDiff: false,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: null,
      };
    }

    if (!codeData?.compare_to) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: "No comparison content available for this selection.",
      };
    }

    return {
      showDiff: true,
      originalContent: codeData.code ?? "",
      modifiedContent: codeData.compare_to.code ?? "",
      isLoadingDiff: false,
      error: null,
    };
  }, [
    codeData,
    compareToCommitId,
  ]);
}

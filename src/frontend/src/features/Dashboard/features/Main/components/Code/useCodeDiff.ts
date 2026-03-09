import { useMemo } from "react";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

function toCodeText(value: string | object | null | undefined): string {
  if (value == null) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return "";
  }
}

function buildCodeContentCandidates(elementId: string): Set<string> {
  const candidates = new Set<string>();
  if (!elementId) return candidates;

  candidates.add(elementId);
  candidates.add(`CodeContentSchema/${elementId}`);
  candidates.add(`CodeContentSchema/${elementId.replace(/\//g, "_")}`);

  return candidates;
}

export interface UseCodeDiffResult {
  showDiff: boolean;
  originalContent: string;
  modifiedContent: string;
  isLoadingDiff: boolean;
  error: string | null;
}

export function useCodeDiff(elementId: string): UseCodeDiffResult {
  const { isOpen, selectedCommitId, diffResult, isLoadingDiff, diffError } =
    useVersioningStore();

  return useMemo(() => {
    const showDiff = Boolean(isOpen && selectedCommitId);
    if (!showDiff) {
      return {
        showDiff: false,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: null,
      };
    }

    if (isLoadingDiff) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: true,
        error: null,
      };
    }

    if (!diffResult) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: diffError ?? "No diff available for this selection.",
      };
    }

    const candidateIds = buildCodeContentCandidates(elementId);
    const contentDiff = diffResult.contentDiffs.find(
      (entry) => entry.contentType === "code" && candidateIds.has(entry.nodeId),
    );

    if (!contentDiff) {
      return {
        showDiff: true,
        originalContent: "",
        modifiedContent: "",
        isLoadingDiff: false,
        error: "No code changes for the selected node in this commit.",
      };
    }

    return {
      showDiff: true,
      originalContent: toCodeText(contentDiff.before),
      modifiedContent: toCodeText(contentDiff.after),
      isLoadingDiff: false,
      error: null,
    };
  }, [diffError, diffResult, elementId, isLoadingDiff, isOpen, selectedCommitId]);
}

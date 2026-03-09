import { useEffect } from "react";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

type VersionDiffController = {
  showDiff: (oldJson: unknown) => void;
  clearDiff: () => void;
};

interface UseDocumentDiffParams {
  projectId?: string;
  nodeId?: string;
  documentId?: string;
  versionDiff?: VersionDiffController | null;
}

export function useDocumentDiff({
  projectId: _projectId,
  nodeId: _nodeId,
  documentId,
  versionDiff,
}: UseDocumentDiffParams) {
  void _projectId;
  void _nodeId;
  const { isOpen, diffResult, isLoadingDiff } = useVersioningStore();
  const isDiffActive = Boolean(isOpen && diffResult);

  useEffect(() => {
    if (!versionDiff) return;
    if (!isDiffActive || !documentId || !diffResult) {
      versionDiff.clearDiff();
      return;
    }
    const contentDiff = diffResult.contentDiffs.find(
      (entry) => entry.nodeId === documentId && entry.contentType === "rich_text"
    );

    if (!contentDiff || contentDiff.before == null) {
      versionDiff.clearDiff();
      return;
    }

    let beforeJson: unknown = contentDiff.before;
    if (typeof beforeJson === "string") {
      try {
        beforeJson = JSON.parse(beforeJson);
      } catch {
        versionDiff.clearDiff();
        return;
      }
    }

    versionDiff.showDiff(beforeJson);
  }, [
    versionDiff,
    isDiffActive,
    documentId,
    diffResult,
  ]);

  return {
    isDiffActive,
    isLoadingContent: isLoadingDiff,
    selectedCommitId: diffResult?.commitAfter ?? null,
    previousCommitId: diffResult?.commitBefore ?? null,
  };
}


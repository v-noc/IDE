import { useEffect } from "react";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import type { DocumentData } from "@/services/documents";

type VersionDiffController = {
  showDiff: (oldJson: unknown) => void;
  clearDiff: () => void;
};

interface UseDocumentDiffParams {
  projectId?: string;
  nodeId?: string;
  document?: DocumentData | null;
  versionDiff?: VersionDiffController | null;
}

export function useDocumentDiff({
  projectId: _projectId,
  nodeId: _nodeId,
  document,
  versionDiff,
}: UseDocumentDiffParams) {
  void _projectId;
  void _nodeId;
  const compareToCommitId = useVersioningStore((s) => s.compareToCommitId);
  const isDiffActive = Boolean(compareToCommitId && document?.compare_to);

  useEffect(() => {
    if (!versionDiff) return;
    if (!isDiffActive || !document?.compare_to) {
      versionDiff.clearDiff();
      return;
    }
    let beforeJson: unknown = document.compare_to.data;
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
    document,
  ]);

  return {
    isDiffActive,
    isLoadingContent: false,
    selectedCommitId: null,
    previousCommitId: null,
  };
}


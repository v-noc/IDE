import React, { useState, useEffect } from "react";
import { X } from "lucide-react";
import { useVersioningStore } from "../store/useVersioningStore";
import CommitHistory from "./CommitHistory";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  useCommitHistory,
  useSelectedCommitDiff,
} from "../hooks/useCommitHistory";
import { mapCommitToDisplay } from "../utils/commitUtils";
import { parseTerminusJsonDiff } from "@/lib/versioningDiff";

const COMMITS_PER_PAGE = 10;

const VersioningPanel: React.FC<{ tabId: string }> = ({ tabId }) => {
  const {
    togglePanel,
    selectedCommitId,
    currentCommitId,
    setCurrentCommitId,
    setSelectedCommit,
    setDiffState,
    clearDiffState,
  } = useVersioningStore();
  const { projectData, selectedNode, secondarySelectedNode } =
    useProjectStore();

  const nodeId = secondarySelectedNode?.[tabId] || selectedNode?.[tabId];
  const [page, setPage] = useState(0);

  useEffect(() => {
    setPage(0);
  }, [projectData?.id, nodeId?.id]);

  useEffect(() => {
    setCurrentCommitId(null);
    setSelectedCommit(null);
    clearDiffState();
  }, [
    projectData?.id,
    nodeId?.id,
    setCurrentCommitId,
    setSelectedCommit,
    clearDiffState,
  ]);

  const {
    data: commits = [],
    isLoading,
    isError,
  } = useCommitHistory(projectData?.id, nodeId?.id, {
    start: page * COMMITS_PER_PAGE,
    count: COMMITS_PER_PAGE,
  });

  useEffect(() => {
    if (page !== 0) return;
    if (isLoading) return;
    if (currentCommitId) return;
    if (commits.length === 0) return;
    setCurrentCommitId(commits[0].id);
  }, [commits, currentCommitId, isLoading, page, setCurrentCommitId]);

  const { data: rawDiff } = useSelectedCommitDiff(
    projectData?.id,
    selectedCommitId,
    currentCommitId,
  );

  useEffect(() => {
    if (
      !selectedCommitId ||
      !currentCommitId ||
      selectedCommitId === currentCommitId
    ) {
      clearDiffState();
      return;
    }
    if (!rawDiff) return;

    const parsed = parseTerminusJsonDiff(rawDiff);

    setDiffState(parsed.nodeDiffs, parsed.parentChildDiffs);
  }, [
    selectedCommitId,
    currentCommitId,
    rawDiff,
    clearDiffState,
    setDiffState,
  ]);

  const displayCommits = commits.map(mapCommitToDisplay);
  const hasNextPage = commits.length === COMMITS_PER_PAGE;
  const hasPrevPage = page > 0;

  return (
    <div className="flex h-full w-full flex-col border-l bg-white shadow-sm transition-all duration-300">
      <div className="flex items-center justify-between border-b px-4 py-3">
        <h2 className="text-lg font-semibold text-slate-800">Commit history</h2>
        <button
          onClick={togglePanel}
          className="rounded-md p-1 hover:bg-slate-100 text-slate-500"
        >
          <X size={20} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto">
        <CommitHistory
          commits={displayCommits}
          isLoading={isLoading}
          isError={isError}
          hasNextPage={hasNextPage}
          hasPrevPage={hasPrevPage}
          page={page}
          onNextPage={() => setPage((p) => p + 1)}
          onPrevPage={() => setPage((p) => Math.max(0, p - 1))}
          emptyMessage={
            !projectData?.id || !nodeId?.id
              ? "Select a node to view commit history"
              : undefined
          }
        />
      </div>
    </div>
  );
};

export default VersioningPanel;

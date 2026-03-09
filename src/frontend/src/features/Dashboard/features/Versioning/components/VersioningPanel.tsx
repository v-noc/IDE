import React, { useState, useEffect } from "react";
import { X } from "lucide-react";
import { useVersioningStore } from "../store/useVersioningStore";
import CommitHistory from "./CommitHistory";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useCommitHistory } from "../hooks/useCommitHistory";
import { mapCommitToDisplay } from "../utils/commitUtils";

const COMMITS_PER_PAGE = 10;

const VersioningPanel: React.FC<{ tabId: string }> = ({ tabId }) => {
  const {
    togglePanel,
    selectedCommitId,
    currentCommitId,
    setCurrentCommitId,
    setSelectedCommit,
    loadParsedDiff,
    clearComparisonState,
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
    clearComparisonState();
  }, [
    projectData?.id,
    nodeId?.id,
    setCurrentCommitId,
    setSelectedCommit,
    clearComparisonState,
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

  useEffect(() => {
    if (!selectedCommitId) {
      clearComparisonState();
      return;
    }
    if (!projectData?.id) return;

    const selectedIndex = commits.findIndex((commit) => commit.id === selectedCommitId);
    if (selectedIndex < 0) {
      clearComparisonState();
      return;
    }

    const previousCommitId = commits[selectedIndex + 1]?.id ?? null;
    if (!previousCommitId) {
      clearComparisonState();
      return;
    }

    void loadParsedDiff({
      projectId: projectData.id,
      beforeCommitId: previousCommitId,
      afterCommitId: selectedCommitId,
    });
  }, [
    projectData?.id,
    commits,
    selectedCommitId,
    clearComparisonState,
    loadParsedDiff,
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

import React from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useVersioningStore } from "../store/useVersioningStore";
import CommitItem from "./CommitItem";
import type { CommitDisplay } from "../store/useVersioningStore";

interface CommitHistoryProps {
  commits: CommitDisplay[];
  isLoading?: boolean;
  isError?: boolean;
  hasNextPage?: boolean;
  hasPrevPage?: boolean;
  page?: number;
  onNextPage?: () => void;
  onPrevPage?: () => void;
  emptyMessage?: string;
}

const CommitHistory: React.FC<CommitHistoryProps> = ({
  commits,
  isLoading,
  isError,
  hasNextPage,
  hasPrevPage,
  page = 0,
  onNextPage,
  onPrevPage,
  emptyMessage,
}) => {
  const { selectedCommitId, setSelectedCommit } = useVersioningStore();

  if (emptyMessage) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 py-8 text-center text-sm text-slate-500">
        {emptyMessage}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 py-8 text-center text-sm text-red-500">
        Failed to load commits
      </div>
    );
  }

  if (isLoading && commits.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 py-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (commits.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 py-8 text-center text-sm text-slate-500">
        No commits yet
      </div>
    );
  }

  return (
    <div className="flex flex-col">
      <div className="flex flex-col px-3 py-4">
        {commits.map((commit, index) => (
          <CommitItem
            key={commit.id}
            commit={commit}
            isLast={index === commits.length - 1}
            isActive={selectedCommitId === commit.id}
            onClick={() => setSelectedCommit(commit.id)}
          />
        ))}
      </div>

      {(hasPrevPage || hasNextPage) && (
        <div className="flex items-center justify-between border-t px-4 py-3">
          <button
            onClick={onPrevPage}
            disabled={!hasPrevPage}
            className="flex items-center gap-1 rounded-md px-2 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
          >
            <ChevronLeft size={16} />
            Previous
          </button>
          <span className="text-xs text-slate-500">Page {page + 1}</span>
          <button
            onClick={onNextPage}
            disabled={!hasNextPage}
            className="flex items-center gap-1 rounded-md px-2 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-transparent"
          >
            Next
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
};

export default CommitHistory;

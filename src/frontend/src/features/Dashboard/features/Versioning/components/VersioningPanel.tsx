import React, { useState, useEffect } from "react";
import { ChevronDown, X } from "lucide-react";
import { useVersioningStore } from "../store/useVersioningStore";
import CommitHistory from "./CommitHistory";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useCommitHistory, type Commit } from "../hooks/useCommitHistory";
import { mapCommitToDisplay } from "../utils/commitUtils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

const COMMITS_PER_PAGE = 10;
const EMPTY_COMMITS: Commit[] = [];

const VersioningPanel: React.FC<{ tabId: string }> = ({ tabId }) => {
  const togglePanel = useVersioningStore((s) => s.togglePanel);
  const historyScope = useVersioningStore((s) => s.historyScopeByTab[tabId]);
  const scopeOverride = useVersioningStore((s) => s.scopeOverrideByTab[tabId]);
  const setScopeOverride = useVersioningStore((s) => s.setScopeOverride);
  const { projectData, selectedNode, secondarySelectedNode } =
    useProjectStore();

  const nodeId = secondarySelectedNode?.[tabId] || selectedNode?.[tabId];
  const itemScopeId =
    historyScope?.scopeType === "docs"
      ? historyScope.scopeId
      : (historyScope?.scopeId ?? nodeId?.id);
  const historyNodeId =
    scopeOverride === "repository" && projectData?.id
      ? `ProjectSchema/${projectData.id}`
      : itemScopeId;
  const [page, setPage] = useState(0);

  useEffect(() => {
    setPage(0);
  }, [projectData?.id, historyNodeId]);

  const {
    data: commits = EMPTY_COMMITS,
    isLoading,
    isError,
  } = useCommitHistory(projectData?.id, historyNodeId ?? undefined, {
    start: page * COMMITS_PER_PAGE,
    count: COMMITS_PER_PAGE,
  });

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
        <div className="px-4 py-2 flex items-center justify-between gap-2 border-b">
          <span className="text-sm text-slate-600">Scope</span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="h-8 min-w-0 gap-1.5 font-normal"
              >
                <span className="truncate">
                  {scopeOverride === "repository"
                    ? "Repository"
                    : "Selected item"}
                </span>
                <ChevronDown className="size-4 shrink-0 opacity-50" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="min-w-[140px]">
              <DropdownMenuItem onClick={() => setScopeOverride(tabId, "item")}>
                Selected item
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => setScopeOverride(tabId, "repository")}
              >
                Repository
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

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
            !projectData?.id || !historyNodeId
              ? "Select content to view commit history"
              : undefined
          }
        />
      </div>
    </div>
  );
};

export default VersioningPanel;

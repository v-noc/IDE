import React, { useState, useEffect } from "react";
import {
  ChevronDown,
  DownloadCloud,
  GitCommit,
  UploadCloud,
  X,
} from "lucide-react";
import { useVersioningStore } from "../store/useVersioningStore";
import CommitHistory from "./CommitHistory";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useCommitHistory, type Commit } from "../hooks/useCommitHistory";
import { mapCommitToDisplay } from "../utils/commitUtils";
import { useVersioningBranches } from "../hooks/useVersioningBranches";
import BranchDropdown from "./BranchDropdown";
import CreateBranchDialog from "./CreateBranchDialog";
import RemoteSyncAuthDialog from "./RemoteSyncAuthDialog";
import { usePushToRemote, usePullFromRemote } from "@/services/versioning";
import { toast } from "sonner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

const COMMITS_PER_PAGE = 10;
const EMPTY_COMMITS: Commit[] = [];

function shortCommit(id: string | null): string {
  if (!id) return "N/A";
  return id.slice(0, 8);
}

const VersioningPanel: React.FC<{ tabId: string }> = ({ tabId }) => {
  const togglePanel = useVersioningStore((s) => s.togglePanel);
  const checkedOutCommitId = useVersioningStore((s) => s.checkedOutCommitId);
  const headCommitId = useVersioningStore((s) => s.headCommitId);
  const historyScope = useVersioningStore((s) => s.historyScopeByTab[tabId]);
  const scopeOverride = useVersioningStore((s) => s.scopeOverrideByTab[tabId]);
  const setScopeOverride = useVersioningStore((s) => s.setScopeOverride);
  const openMergeMode = useVersioningStore((s) => s.openMergeMode);
  const { projectData, selectedNode, secondarySelectedNode } =
    useProjectStore();

  const nodeId = secondarySelectedNode?.[tabId] || selectedNode?.[tabId];
  const itemScopeId =
    historyScope?.scopeType === "docs" && historyScope.scopeId
      ? historyScope.scopeId
      : (historyScope?.scopeId ?? nodeId?.id);
  const historyNodeId =
    scopeOverride === "repository" && projectData?.id
      ? `ProjectSchema/${projectData.id}`
      : itemScopeId;
  const [page, setPage] = useState(0);
  const [isCreateBranchOpen, setIsCreateBranchOpen] = useState(false);
  const [remoteSyncMode, setRemoteSyncMode] = useState<"push" | "pull" | null>(
    null,
  );

  const {
    currentBranch,
    availableBranches,
    switchBranch,
    createBranch,
    isCreatingBranch,
    isLoadingBranches,
  } = useVersioningBranches(projectData?.id);

  const pushMutation = usePushToRemote(projectData?.id, currentBranch);
  const pullMutation = usePullFromRemote(projectData?.id, currentBranch);

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
  const displayedCommitId = checkedOutCommitId ?? headCommitId;

  return (
    <div className="flex h-full w-full flex-col border-l bg-white shadow-sm transition-all duration-300">
      <div className="border-b px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-slate-800">
            Commit history
          </h2>
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              onClick={togglePanel}
              className="rounded-md p-1 text-slate-500 hover:bg-slate-100"
              aria-label="Close panel"
            >
              <X size={20} />
            </button>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-1 px-2 text-xs"
            disabled={!projectData?.id}
            onClick={() => setRemoteSyncMode("push")}
            title="Push to origin"
          >
            <UploadCloud className="size-3.5" />
            Push
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-8 gap-1 px-2 text-xs"
            disabled={!projectData?.id}
            onClick={() => setRemoteSyncMode("pull")}
            title="Pull from origin"
          >
            <DownloadCloud className="size-3.5" />
            Pull
          </Button>
        </div>
        <div className="mt-3 flex flex-col gap-1">
          <div className="flex min-w-0 items-center justify-between w-full gap-1">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
              Branch
            </span>
            <BranchDropdown
              branches={availableBranches.map((b) => ({
                id: b.id,
                name: b.name,
                isCurrent: b.name === currentBranch,
              }))}
              currentBranch={currentBranch}
              onSelectBranch={switchBranch}
              onNewBranch={() => setIsCreateBranchOpen(true)}
              onMergeBranches={() => {
                const firstCandidate = availableBranches.find(
                  (candidate) => candidate.name !== currentBranch,
                );
                openMergeMode({
                  sourceBranch: currentBranch,
                  targetBranch: firstCandidate?.name ?? null,
                });
              }}
              isLoading={isLoadingBranches}
              triggerClassName="h-7 justify-start gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 font-normal text-sm text-slate-800 hover:bg-slate-50"
            />
          </div>
          <div className="flex min-w-0 items-center justify-between w-full gap-1">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
              Current commit
            </span>
            <span className="inline-flex h-7 min-w-0 items-center gap-1.5 rounded-md border  border-slate-200 bg-white px-2.5 font-mono text-xs text-slate-700">
              <GitCommit className="size-3.5 shrink-0 text-slate-500" />
              {shortCommit(displayedCommitId)}
            </span>
          </div>
          <div className="flex min-w-0 items-center justify-between w-full gap-1">
            <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
              Scope
            </span>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 justify-start gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 font-normal text-sm text-slate-800 hover:bg-slate-50"
                >
                  <span className="truncate text-xs">
                    {scopeOverride === "repository"
                      ? "Repository"
                      : "Selected item"}
                  </span>
                  <ChevronDown className="size-4 shrink-0 opacity-50" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="min-w-[140px]">
                <DropdownMenuItem
                  onClick={() => setScopeOverride(tabId, "item")}
                >
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
        </div>
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
            !projectData?.id || !historyNodeId
              ? "Select content to view commit history"
              : undefined
          }
        />
      </div>
      <CreateBranchDialog
        open={isCreateBranchOpen}
        onOpenChange={setIsCreateBranchOpen}
        onCreate={createBranch}
        isCreating={isCreatingBranch}
      />
      <RemoteSyncAuthDialog
        open={remoteSyncMode != null}
        onOpenChange={(open) => {
          if (!open) setRemoteSyncMode(null);
        }}
        mode={remoteSyncMode ?? "push"}
        isPending={pushMutation.isPending || pullMutation.isPending}
        onConfirm={(auth) => {
          const remote_auth = {
            type: auth.type,
            key: auth.key,
            ...(auth.type === "http_basic" ? { username: auth.username } : {}),
          };
          const onSettled = () => setRemoteSyncMode(null);
          if (remoteSyncMode === "push") {
            pushMutation.mutate(remote_auth, {
              onSuccess: () => {
                toast.success("Push completed");
                onSettled();
              },
              onError: (err) => {
                toast.error(err instanceof Error ? err.message : "Push failed");
              },
            });
          } else if (remoteSyncMode === "pull") {
            pullMutation.mutate(remote_auth, {
              onSuccess: () => {
                toast.success("Pull completed");
                onSettled();
              },
              onError: (err) => {
                toast.error(err instanceof Error ? err.message : "Pull failed");
              },
            });
          }
        }}
      />
    </div>
  );
};

export default VersioningPanel;

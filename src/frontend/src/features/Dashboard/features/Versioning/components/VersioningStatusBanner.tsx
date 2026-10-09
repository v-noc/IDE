import {
  GitBranch,
  GitCommit,
  ArrowLeftRight,
  X,
} from "lucide-react";
import { useVersioningBanner } from "../hooks/useVersioningBanner";
import { Button } from "@/components/ui/button";
import { VersioningStatusActionsMenu } from "./VersioningStatusActionsMenu";
import { useMergeBranchComparison } from "../hooks/useMergeBranchComparison";
import { MergeBranchStatusSection } from "./MergeBranchStatusSection";

const VersioningStatusBanner = () => {
  const {
    branch,
    checkedOutCommitId,
    compareToCommitId,
    targetCommitId,
    isVisible,
    isComparing,
    isMergeMode,
    showAffectedOnly,
    shortCommit,
    swapCompare,
    clearCompare,
    closeBanner,
    setShowAffectedOnly,
  } = useVersioningBanner();
  const {
    sourceBranch,
    targetBranch,
    mergeCandidates,
    isLoadingBranches,
    selectMergeTargetBranch,
    swapMergeBranches,
  } = useMergeBranchComparison();

  if (!isVisible) return null;
  // Dynamic status text logic
  const getStatusText = () => {
    if (isMergeMode) return "Preparing branch merge";
    if (isComparing) return "Comparing versions";
    if (checkedOutCommitId) return "Viewing historical snapshot"; // Your "temporary" text
    return "Project is live";
  };

  return (
    <div className="flex items-center justify-between sm:flex-row flex-col border-b border-border bg-muted/95 px-4 py-1.5 text-xs text-muted-foreground shadow-sm">
      {/* LEFT: Context/Path */}
      <div className=" items-center gap-2 overflow-hidden sm:flex hidden">
        <div className="flex h-2 w-2 animate-pulse rounded-full bg-chart-4" />
        <span className="font-medium text-muted-foreground">{getStatusText()}</span>
      </div>

      {/* CENTER: Status & Comparison */}
      <div className="flex items-center justify-center gap-3 sm:flex-row flex-col">
        <div className="flex items-center gap-2">
          {/* Branch */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              On
            </span>
            <span className="inline-flex items-center gap-1 rounded-md border border-border bg-card px-2 py-0.5 font-medium text-foreground shadow-sm">
              <GitBranch className="size-3 text-muted-foreground" />
              {branch}
            </span>
          </div>

          {/* Checkout Status */}
          {checkedOutCommitId && !isMergeMode && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                at
              </span>
              <span className="inline-flex items-center gap-1 rounded-md border border-chart-4/40 bg-chart-4/15 px-2 py-0.5 font-mono text-chart-4 shadow-sm">
                <GitCommit className="size-3 text-chart-4" />
                {shortCommit(checkedOutCommitId)}
              </span>
            </div>
          )}
        </div>

        {/* Comparison Section */}
        {isComparing && !isMergeMode && (
          <div className="flex items-center gap-2 border-l border-border pl-3">
            <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground sm:block hidden">
              Comparing
            </span>
            <div className="flex items-center gap-1 rounded-full border border-chart-5/30 bg-chart-5/10 p-0.5 pr-1 shadow-sm">
              <span className="inline-flex items-center gap-1 rounded-full bg-card px-2 py-0.5 font-mono text-chart-5 border border-chart-5/30">
                {shortCommit(targetCommitId)}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="size-5 rounded-full hover:bg-chart-5/15"
                onClick={swapCompare}
                title="Swap direction"
              >
                <ArrowLeftRight className="size-3 text-chart-5" />
              </Button>
              <span className="inline-flex items-center gap-1 rounded-full bg-card px-2 py-0.5 font-mono text-chart-5 border border-chart-5/30">
                {shortCommit(compareToCommitId)}
              </span>
              <button
                onClick={clearCompare}
                className="ml-1 rounded-full p-0.5 hover:bg-chart-5/15 text-chart-5"
              >
                <X className="size-3" />
              </button>
            </div>
          </div>
        )}
        {isMergeMode && (
          <MergeBranchStatusSection
            sourceBranch={sourceBranch}
            targetBranch={targetBranch}
            isLoadingBranches={isLoadingBranches}
            mergeCandidates={mergeCandidates}
            onSelectTarget={selectMergeTargetBranch}
            onSwapBranches={swapMergeBranches}
            onClose={closeBanner}
          />
        )}
      </div>

      {/* RIGHT: Actions */}
      <div className="flex items-center justify-end gap-1">
        {!isMergeMode && (
          <>
            <div className="mx-1 h-4 w-px bg-border" />
            <VersioningStatusActionsMenu
              isComparing={isComparing}
              hasCompareTo={Boolean(compareToCommitId)}
              hasCheckedOutCommit={Boolean(checkedOutCommitId)}
              showAffectedOnly={showAffectedOnly}
              onToggleAffectedOnly={setShowAffectedOnly}
              onFlipComparison={swapCompare}
            />
          </>
        )}

        <Button
          variant="ghost"
          size="icon"
          className="size-7 text-muted-foreground hover:text-destructive"
          onClick={closeBanner}
        >
          <X className="size-4" />
        </Button>
      </div>
    </div>
  );
};

export default VersioningStatusBanner;

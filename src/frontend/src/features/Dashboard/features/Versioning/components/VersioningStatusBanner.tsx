import {
  GitBranch,
  GitCommit,
  ArrowLeftRight,
  X,
  MoreVertical,
  FileDiff,
  History,
  Download,
} from "lucide-react";
import { useVersioningBanner } from "../hooks/useVersioningBanner";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

const VersioningStatusBanner = () => {
  const {
    branch,
    checkedOutCommitId,
    compareToCommitId,
    targetCommitId,
    isVisible,
    isComparing,
    shortCommit,
    swapCompare,
    clearCompare,
    closeBanner,
  } = useVersioningBanner();

  if (!isVisible) return null;

  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-200 bg-slate-50/95 px-3 py-2 text-xs text-slate-700 shadow-sm">
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
        {/* Branch / Checkout status */}
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2 py-1 font-medium text-slate-800 shadow-xs">
            <GitBranch className="size-3.5 text-slate-500" />
            {branch}
          </span>
          {checkedOutCommitId ? (
            <span className="inline-flex items-center gap-1.5 rounded-md border border-amber-200 bg-amber-50 px-2 py-1 font-mono text-amber-900">
              <GitCommit className="size-3.5 text-amber-600" />
              {shortCommit(checkedOutCommitId)}
            </span>
          ) : (
            <span className="text-slate-500">Following HEAD</span>
          )}
        </div>

        {/* Compare section */}
        {isComparing && (
          <div className="flex items-center gap-1">
            <span className="text-slate-500">·</span>
            <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white/80 px-2 py-1 shadow-xs">
              <span className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-slate-700">
                <GitCommit className="size-3 text-slate-500" />
                {shortCommit(compareToCommitId)}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="size-6 shrink-0"
                onClick={swapCompare}
                title="Swap comparison direction"
              >
                <ArrowLeftRight className="size-3.5 text-slate-500" />
              </Button>
              <span className="inline-flex items-center gap-1 rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-slate-700">
                <GitCommit className="size-3 text-slate-500" />
                {shortCommit(targetCommitId)}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="size-6 shrink-0 text-slate-400 hover:text-slate-600"
                onClick={clearCompare}
                title="Remove comparison"
              >
                <X className="size-3" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Right side: menu + close */}
      <div className="flex shrink-0 items-center gap-0.5">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-slate-500 hover:bg-slate-200/60 hover:text-slate-700"
              title="More options"
            >
              <MoreVertical className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-[180px]">
            <DropdownMenuItem>
              <History className="size-4" />
              View full history
            </DropdownMenuItem>
            {isComparing && (
              <DropdownMenuItem>
                <FileDiff className="size-4" />
                Export diff
              </DropdownMenuItem>
            )}
            <DropdownMenuItem>
              <Download className="size-4" />
              Download snapshot
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          variant="ghost"
          size="icon"
          className="size-7 text-slate-500 hover:bg-slate-200/60 hover:text-slate-700"
          onClick={closeBanner}
          title="Close versioning banner"
        >
          <X className="size-4" />
        </Button>
      </div>
    </div>
  );
};

export default VersioningStatusBanner;

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
  // Dynamic status text logic
  const getStatusText = () => {
    if (isComparing) return "Comparing versions";
    if (checkedOutCommitId) return "Viewing historical snapshot"; // Your "temporary" text
    return "Project is live";
  };

  return (
    <div className="flex items-center justify-between sm:flex-row flex-col border-b border-slate-200 bg-slate-50/95 px-4 py-1.5 text-xs text-slate-600 shadow-sm">
      {/* LEFT: Context/Path */}
      <div className=" items-center gap-2 overflow-hidden sm:flex hidden">
        <div className="flex h-2 w-2 animate-pulse rounded-full bg-amber-400" />
        <span className="font-medium text-slate-500">{getStatusText()}</span>
      </div>

      {/* CENTER: Status & Comparison */}
      <div className="flex items-center justify-center gap-3 sm:flex-row flex-col">
        <div className="flex items-center gap-2">
          {/* Branch */}
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              On
            </span>
            <span className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-0.5 font-medium text-slate-800 shadow-sm">
              <GitBranch className="size-3 text-slate-400" />
              {branch}
            </span>
          </div>

          {/* Checkout Status */}
          {checkedOutCommitId && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
                at
              </span>
              <span className="inline-flex items-center gap-1 rounded-md border border-amber-200 bg-amber-50/50 px-2 py-0.5 font-mono text-amber-900 shadow-sm">
                <GitCommit className="size-3 text-amber-500" />
                {shortCommit(checkedOutCommitId)}
              </span>
            </div>
          )}
        </div>

        {/* Comparison Section */}
        {isComparing && (
          <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400 sm:block hidden">
              Comparing
            </span>
            <div className="flex items-center gap-1 rounded-full border border-indigo-100 bg-indigo-50/30 p-0.5 pr-1 shadow-sm">
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 font-mono text-indigo-700 border border-indigo-100">
                {shortCommit(compareToCommitId)}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="size-5 rounded-full hover:bg-indigo-100"
                onClick={swapCompare}
                title="Swap direction"
              >
                <ArrowLeftRight className="size-3 text-indigo-500" />
              </Button>
              <span className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 font-mono text-indigo-700 border border-indigo-100">
                {shortCommit(targetCommitId)}
              </span>
              <button
                onClick={clearCompare}
                className="ml-1 rounded-full p-0.5 hover:bg-indigo-100 text-indigo-400"
              >
                <X className="size-3" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* RIGHT: Actions */}
      <div className="flex items-center justify-end gap-1">
        <div className="mx-1 h-4 w-px bg-slate-200" />

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="size-7 text-slate-400"
            >
              <MoreVertical className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {isComparing && (
              <DropdownMenuItem className="gap-2">
                <FileDiff className="size-4 opacity-70" /> Export Diff
              </DropdownMenuItem>
            )}
            <DropdownMenuItem className="gap-2">
              <Download className="size-4 opacity-70" /> Download Snapshot
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          variant="ghost"
          size="icon"
          className="size-7 text-slate-400 hover:text-red-500"
          onClick={closeBanner}
        >
          <X className="size-4" />
        </Button>
      </div>
    </div>
  );
};

export default VersioningStatusBanner;

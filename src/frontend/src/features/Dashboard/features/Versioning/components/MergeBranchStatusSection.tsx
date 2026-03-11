import { ArrowLeftRight, ChevronDown, GitBranch, GitMerge, X } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

interface MergeBranchStatusSectionProps {
  sourceBranch: string;
  targetBranch: string | null;
  isLoadingBranches: boolean;
  mergeCandidates: Array<{ id: string; name: string }>;
  onSelectTarget: (name: string) => void;
  onSwapBranches: () => void;
  onClose: () => void;
}

export function MergeBranchStatusSection({
  sourceBranch,
  targetBranch,
  isLoadingBranches,
  mergeCandidates,
  onSelectTarget,
  onSwapBranches,
  onClose,
}: MergeBranchStatusSectionProps) {
  return (
    <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
      <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400 sm:block hidden">
        Merge
      </span>
      <div className="flex items-center gap-1 rounded-full border border-emerald-100 bg-emerald-50/30 p-0.5 pr-1 shadow-sm">
        <span className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-white px-2 py-0.5 text-slate-700">
          <GitBranch className="size-3 text-emerald-500" />
          <span className="max-w-[120px] truncate">{sourceBranch}</span>
        </span>

        <Button
          variant="ghost"
          size="icon"
          className="size-5 rounded-full text-emerald-500 hover:bg-emerald-100"
          onClick={onSwapBranches}
          title="Swap merge direction"
          disabled={!targetBranch}
        >
          <ArrowLeftRight className="size-3" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-white px-2 py-0.5 text-slate-700 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-70"
              disabled={isLoadingBranches || mergeCandidates.length === 0}
            >
              <GitMerge className="size-3 text-emerald-500" />
              <span className="max-w-[120px] truncate">
                {targetBranch ?? "Select branch"}
              </span>
              <ChevronDown className="size-3 text-emerald-500" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="min-w-[200px]">
            {mergeCandidates.length === 0 ? (
              <DropdownMenuItem disabled>No branches available</DropdownMenuItem>
            ) : (
              mergeCandidates.map((candidate) => (
                <DropdownMenuItem
                  key={candidate.id}
                  onClick={() => onSelectTarget(candidate.name)}
                  className="gap-2"
                >
                  <GitBranch className="size-4 opacity-70" />
                  {candidate.name}
                </DropdownMenuItem>
              ))
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        <button
          onClick={onClose}
          className="ml-1 rounded-full p-0.5 text-emerald-500 hover:bg-emerald-100"
          title="Close merge banner"
        >
          <X className="size-3" />
        </button>
      </div>
    </div>
  );
}

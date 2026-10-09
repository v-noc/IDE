import React from "react";
import { ChevronDown, GitBranch, GitMerge, Plus } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface BranchItem {
  id: string;
  name: string;
  isCurrent?: boolean;
}

export interface BranchDropdownProps {
  branches: BranchItem[];
  currentBranch: string;
  onSelectBranch: (name: string) => void;
  onNewBranch?: () => void;
  onMergeBranches?: () => void;
  isLoading?: boolean;
  className?: string;
  triggerClassName?: string;
}

const BranchDropdown: React.FC<BranchDropdownProps> = ({
  branches,
  currentBranch,
  onSelectBranch,
  onNewBranch,
  onMergeBranches,
  isLoading = false,
  className,
  triggerClassName,
}) => {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md border border-border bg-card px-2.5 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-accent",
            triggerClassName,
          )}
          disabled={isLoading}
        >
          <GitBranch className="size-4 shrink-0 text-muted-foreground" />
          <span className="min-w-0 flex-1 truncate text-left text-xs">
            {currentBranch}
          </span>
          <ChevronDown className="size-4 shrink-0 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="start"
        className={cn("min-w-[200px]", className)}
      >
        <DropdownMenuLabel className="text-xs font-medium text-muted-foreground">
          Branches
        </DropdownMenuLabel>
        {branches.map((branch) => (
          <DropdownMenuItem
            key={branch.id}
            onClick={() => onSelectBranch(branch.name)}
            className={`flex items-center gap-2 ${
              branch.name === currentBranch ? "bg-accent" : ""
            }`}
          >
            <GitBranch className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate text-sm">{branch.name}</span>
          </DropdownMenuItem>
        ))}
        {(onNewBranch ?? onMergeBranches) && (
          <>
            <DropdownMenuSeparator />
            {onNewBranch && (
              <DropdownMenuItem onClick={onNewBranch} className="gap-2 text-sm">
                <Plus className="size-4 shrink-0 text-muted-foreground " />
                New Branch
              </DropdownMenuItem>
            )}
            {onMergeBranches && (
              <DropdownMenuItem
                onClick={onMergeBranches}
                className="gap-2 text-sm"
              >
                <GitMerge className="size-4 shrink-0 text-muted-foreground" />
                Merge Branches
              </DropdownMenuItem>
            )}
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default BranchDropdown;

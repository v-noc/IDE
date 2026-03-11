import {
  ArrowLeftRight,
  Download,
  FileDiff,
  GitCommit,
  MoreVertical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface VersioningStatusActionsMenuProps {
  isComparing: boolean;
  hasCompareTo: boolean;
  hasCheckedOutCommit: boolean;
  showAffectedOnly: boolean;
  onToggleAffectedOnly: (next: boolean) => void;
  onFlipComparison: () => void;
}

export function VersioningStatusActionsMenu({
  isComparing,
  hasCompareTo,
  hasCheckedOutCommit,
  showAffectedOnly,
  onToggleAffectedOnly,
  onFlipComparison,
}: VersioningStatusActionsMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="size-7 text-slate-400">
          <MoreVertical className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          className="gap-2"
          onSelect={onFlipComparison}
          disabled={!hasCompareTo}
        >
          <ArrowLeftRight className="size-4 opacity-70" /> Flip Comparison
        </DropdownMenuItem>
        <DropdownMenuCheckboxItem
          checked={showAffectedOnly}
          onCheckedChange={(checked) => onToggleAffectedOnly(Boolean(checked))}
        >
          Show affected only
        </DropdownMenuCheckboxItem>
        <DropdownMenuItem className="gap-2" disabled={!hasCheckedOutCommit}>
          <GitCommit className="size-4 opacity-70" /> Hard reset to checked out
          commit
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

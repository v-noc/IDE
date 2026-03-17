import { memo } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { DynamicIcon } from "@/components/DynamicIcon";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import getIcons from "@/features/Dashboard/utils/getIcons";
import type { ContainerNodeTree, CallNodeTree } from "@/types/project";

interface NodeRowProps {
  node: ContainerNodeTree;
  isOpen: boolean;
  isSelected: boolean;
  hasChildren: boolean;
  iconColor: string;
  onToggle: (e: React.MouseEvent) => void;
  onClick: () => void;
}

export const NodeRow = memo(function NodeRow({
  node,
  isOpen,
  isSelected,
  hasChildren,
  iconColor,
  onToggle,
  onClick,
}: NodeRowProps) {
  const diffStatus = node.status ?? "none";
  const iconName =
    node.icon ||
    getIcons(
      node.node_type === "call"
        ? ((node as CallNodeTree).target?.node_type ?? "call")
        : node.node_type,
    );

  const row = (
    <li
      onClick={onClick}
      className={cn(
        "flex items-center space-x-1 rounded-md p-1 cursor-pointer",
        "transition-all duration-200",
        diffStatus === "added" || diffStatus === "removed"
          ? "hover:bg-white/10"
          : diffStatus === "modified"
            ? "hover:bg-amber-200/60"
            : "hover:bg-black/5",
      )}
    >
      {/* Toggle */}
      {hasChildren ? (
        <button
          onClick={onToggle}
          className="p-0.5 rounded-md hover:bg-black/10"
          aria-label={isOpen ? "Collapse" : "Expand"}
        >
          <ChevronRight
            className={cn(
              "h-4 w-4 transition-transform duration-200",
              isOpen && "rotate-90",
            )}
          />
        </button>
      ) : (
        <div className="w-4 h-4" />
      )}

      {/* Icon */}
      <DynamicIcon
        iconName={iconName}
        className="h-4 w-4 shrink-0"
        color={iconColor}
      />

      {/* Name */}
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            "text-sm truncate block",
            isSelected ? "font-semibold" : "font-medium",
            diffStatus === "removed" && "opacity-90",
          )}
        >
          {node.name}
        </span>
      </div>
    </li>
  );

  // Wrap with tooltip only if has description
  const description =
    node.node_type === "call"
      ? (node as CallNodeTree).target?.description
      : node.description;
  if (description) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{row}</TooltipTrigger>
        <TooltipContent side="right">
          <p className="max-w-xs">{description}</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  return row;
});

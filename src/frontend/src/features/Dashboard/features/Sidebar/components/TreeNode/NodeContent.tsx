import { memo } from "react";
import { cn } from "@/lib/utils";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import { TooltipProvider } from "@/components/ui/tooltip";
import { NodeRow } from "./NodeRow";
import { NodeChildren } from "./NodeChildren";
import { useNodeStyle } from "@/features/Dashboard/hooks/useNodeStyle";
import type { ContainerNodeTree } from "@/types/project";

interface NodeContentProps {
  node: ContainerNodeTree;
  tabId: string;
  isOpen: boolean;
  isSelected: boolean;
  isActive: boolean;
  hasChildren: boolean;
  nestingLevel: number;
  handleToggle: (e: React.MouseEvent) => void;
  handleSelectNode: () => void;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
  showLoadMore?: boolean;
  loadMorePending?: boolean;
  onLoadMore?: () => void;
  /** Lazy code descendants request in flight and no rows to show yet. */
  showLazyChildrenSkeleton?: boolean;
}

export const NodeContent = memo(function NodeContent({
  node,
  tabId,
  isOpen,
  isSelected,
  isActive,
  hasChildren,
  nestingLevel,
  handleToggle,
  handleSelectNode,
  childFilter,
  onSelect,
  showLoadMore,
  loadMorePending,
  onLoadMore,
  showLazyChildrenSkeleton = false,
}: NodeContentProps) {
  const style = useNodeStyle(node);
  const diffStatus = node.status ?? "none";
  const diffClass =
    diffStatus === "added"
      ? "border-emerald-600/90 bg-emerald-600 text-white"
      : diffStatus === "removed"
        ? "border-rose-700/90 bg-rose-700 text-white opacity-50"
        : diffStatus === "modified"
          ? "border-amber-500/90 bg-amber-100 text-amber-950"
          : "";
  const iconColor =
    diffStatus === "added" || diffStatus === "removed"
      ? "#ffffff"
      : diffStatus === "modified"
        ? "#78350f"
        : style.iconColor;

  return (
    <TooltipProvider>
      <Collapsible open={isOpen}>
        <div
          className={cn(
            "rounded-lg p-1 transition-all duration-200 border",
            "mx-1 my-0.5",
            nestingLevel > 0 && "ml-2",
            diffClass,
            isSelected && "ring-1 ring-blue-500/80",
            isActive && "ring-2 ring-blue-600",
          )}
          style={{
            backgroundColor:
              diffStatus === "none" || diffStatus === "unchanged"
                ? style.backgroundColor
                : undefined,
            color:
              diffStatus === "none" || diffStatus === "unchanged"
                ? style.color
                : undefined,
            borderColor:
              diffStatus === "none" || diffStatus === "unchanged"
                ? style.borderColor
                : undefined,
          }}
          data-node-key={node.id}
        >
          <NodeRow
            node={node}
            isOpen={isOpen}
            isSelected={isSelected}
            hasChildren={hasChildren}
            iconColor={iconColor}
            onToggle={handleToggle}
            onClick={handleSelectNode}
          />

          {hasChildren && (
            <CollapsibleContent>
              <NodeChildren
                node={node}
                tabId={tabId}
                nestingLevel={nestingLevel}
                childFilter={childFilter}
                onSelect={onSelect}
              />
              {showLazyChildrenSkeleton ? (
                <ul
                  className="pl-2 pt-1 space-y-1"
                  aria-busy="true"
                  aria-label="Loading nested items"
                >
                  {[0, 1, 2].map((i) => (
                    <li key={i} className="flex items-center gap-2 py-0.5">
                      <Skeleton className="size-4 shrink-0 rounded" />
                      <Skeleton className="h-3.5 flex-1 max-w-[min(100%,14rem)] rounded-md" />
                    </li>
                  ))}
                </ul>
              ) : null}
              {showLoadMore && onLoadMore ? (
                <div className="pl-6 pt-1">
                  <button
                    type="button"
                    className="text-xs text-muted-foreground hover:text-foreground underline disabled:opacity-50"
                    disabled={loadMorePending}
                    onClick={(e) => {
                      e.stopPropagation();
                      onLoadMore();
                    }}
                  >
                    {loadMorePending ? "Loading…" : "Load more"}
                  </button>
                </div>
              ) : null}
            </CollapsibleContent>
          )}
        </div>
      </Collapsible>
    </TooltipProvider>
  );
});

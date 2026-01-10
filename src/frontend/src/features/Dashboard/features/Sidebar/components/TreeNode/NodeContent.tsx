import { memo } from "react";
import { cn } from "@/lib/utils";
import { Collapsible, CollapsibleContent } from "@/components/ui/collapsible";
import { TooltipProvider } from "@/components/ui/tooltip";
import { NodeRow } from "./NodeRow";
import { NodeChildren } from "./NodeChildren";
import { useNodeStyle } from "@/features/Dashboard/hooks/useNodeStyle";
import type { ContainerNodeTree } from "@/types/project";

interface NodeContentProps {
  node: ContainerNodeTree;
  isOpen: boolean;
  isSelected: boolean;
  isActive: boolean;
  hasChildren: boolean;
  nestingLevel: number;
  handleToggle: (e: React.MouseEvent) => void;
  handleSelectNode: () => void;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const NodeContent = memo(function NodeContent({
  node,
  isOpen,
  isSelected,
  isActive,
  hasChildren,
  nestingLevel,
  handleToggle,
  handleSelectNode,
  childFilter,
  onSelect,
}: NodeContentProps) {
  const style = useNodeStyle(node);

  return (
    <TooltipProvider>
      <Collapsible open={isOpen}>
        <div
          className={cn(
            "rounded-lg p-1 transition-all duration-200 border",
            "mx-1 my-0.5",
            nestingLevel > 0 && "ml-2",
            isSelected && "ring-1 ring-blue-500/80",
            isActive && "ring-2 ring-blue-600"
          )}
          style={{
            backgroundColor: style.backgroundColor,
            color: style.color,
            borderColor: style.borderColor,
          }}
          data-node-key={node._key}
        >
          <NodeRow
            node={node}
            isOpen={isOpen}
            isSelected={isSelected}
            hasChildren={hasChildren}
            iconColor={style.iconColor}
            onToggle={handleToggle}
            onClick={handleSelectNode}
          />

          {hasChildren && (
            <CollapsibleContent>
              <NodeChildren
                node={node}
                nestingLevel={nestingLevel}
                childFilter={childFilter}
                onSelect={onSelect}
              />
            </CollapsibleContent>
          )}
        </div>
      </Collapsible>
    </TooltipProvider>
  );
});

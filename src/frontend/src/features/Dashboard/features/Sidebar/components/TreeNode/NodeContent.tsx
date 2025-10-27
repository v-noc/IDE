import React, { useMemo } from "react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DynamicIcon } from "@/components/DynamicIcon";
import getIcons from "@/features/Dashboard/utils/getIcons";
import type { CallNodeTree, ContainerNodeTree } from "@/types/project";
import getNodeStyle from "@/features/Dashboard/utils/getNodeStyle";
import { TreeNode } from ".";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";

type NodeContentProps = {
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
};

export const NodeContent = ({
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
}: NodeContentProps) => {
  const { projectData } = useProjectStore();

  const nodeStyle = useMemo(() => {
    let currentNode = node;
    if (node.target) {
      const nodeByKey = findNodeByKey(projectData, node.target._key);
      if (nodeByKey) {
        currentNode = nodeByKey;
      }
    }
    return getNodeStyle(currentNode);
  }, [node, projectData]);

  const currentStyle = {
    backgroundColor: nodeStyle.cardColor,
    color: nodeStyle.color,
    borderColor: nodeStyle.borderColor,
  };

  // Check if this node has a description (for virtual folders)
  const hasDescription = node.description;

  const nodeContent = (
    <li
      onClick={handleSelectNode}
      className={cn(
        "flex items-center space-x-1 rounded-md p-1 transition-all duration-200 cursor-pointer ",
        "hover:bg-black/5"
      )}
    >
      {hasChildren ? (
        <CollapsibleTrigger
          onClick={handleToggle}
          className="p-0.5 rounded-md hover:bg-black/10 "
        >
          <ChevronRight
            className={cn(
              "h-4 w-4 transition-transform duration-200",
              isOpen && "rotate-90"
            )}
          />
        </CollapsibleTrigger>
      ) : (
        <div className="w-4 h-4 "> </div>
      )}

      <DynamicIcon
        iconName={
          node.icon ||
          getIcons(
            node.node_type === "call"
              ? (node as CallNodeTree).target?.node_type ?? "call"
              : node.node_type
          )
        }
        className={cn("h-4 w-4 flex-shrink-0")}
        color={nodeStyle.iconColor}
      />
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            "text-sm truncate block",
            isSelected ? "font-semibold" : "font-medium"
          )}
        >
          {node.name}
        </span>
      </div>
    </li>
  );

  return (
    <Collapsible open={isOpen}>
      <div
        className={cn(
          "rounded-lg p-1 transition-all duration-200 border ",
          "mx-1 my-0.5",
          nestingLevel > 0 && "ml-2",

          isSelected && "ring-1 ring-blue-500/80",
          isActive && "ring-2 ring-blue-600"
        )}
        style={currentStyle}
        data-node-key={node._key}
      >
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>{nodeContent}</TooltipTrigger>
            {hasDescription && (
              <TooltipContent>
                <p className="max-w-xs">{node.description}</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
        {hasChildren && (
          <CollapsibleContent>
            <ul className="pl-2 pt-1 space-y-1">
              {node.children
                ?.filter((n) => (childFilter ? childFilter(n) : true))
                .sort((a, b) => {
                  const getRank = (n: ContainerNodeTree) =>
                    n.node_type === "folder"
                      ? 0
                      : n.node_type === "file"
                      ? 1
                      : 2;
                  const rankDiff = getRank(a) - getRank(b);
                  if (rankDiff !== 0) return rankDiff;
                  return a.name.localeCompare(b.name);
                })
                .map((child) => (
                  <TreeNode
                    key={child._key}
                    node={child}
                    nestingLevel={nestingLevel + 1}
                    childFilter={childFilter}
                    onSelect={onSelect}
                  />
                ))}
            </ul>
          </CollapsibleContent>
        )}
      </div>
    </Collapsible>
  );
};

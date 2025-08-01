import React from "react";

import useProjectStore from "@/stores/useProjectStore";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { DynamicIcon } from "@/components/DynamicIcon";
import getIcons from "@/features/Dashboard/utils/getIcons";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import getNodeStyle from "@/features/Dashboard/utils/getNodeStyle";

interface TreeNodeProps {
  node: ProjectTreeResponse;
  nestingLevel?: number;
}

export const TreeNode = ({ node, nestingLevel = 0 }: TreeNodeProps) => {
  const {
    selectedNode,
    setSelectedNode,
    activeNodeId,
    expandedNodeIds,
    toggleNodeExpansion,
  } = useProjectStore();

  const isOpen = expandedNodeIds.has(node.key);
  const nodeStyle = getNodeStyle(node);
  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();

    toggleNodeExpansion(node.key);
  };

  const isSelected = selectedNode?.key === node.key;
  const isActive = activeNodeId === node.key;
  const hasChildren = node.children && node.children.length > 0;

  const handleSelectNode = () => {
    setSelectedNode(node);
  };

  const baseStyle = {
    backgroundColor: nodeStyle.backgroundColor,
    color: nodeStyle.color,
    borderColor: nodeStyle.borderColor,
  };

  const selectedStyle = {
    backgroundColor: nodeStyle.backgroundColor,
    color: nodeStyle.color,
    borderColor: nodeStyle.borderColor,
  };

  const activeStyle = {
    backgroundColor: nodeStyle.backgroundColor,
    color: nodeStyle.color,
    borderColor: nodeStyle.borderColor,
  };

  const currentStyle = isActive
    ? activeStyle
    : isSelected
    ? selectedStyle
    : baseStyle;

  return (
    <Collapsible open={isOpen}>
      <div
        className={cn(
          "rounded-lg p-1 transition-all duration-200 border",
          "mx-1 my-0.5",
          nestingLevel > 0 && "ml-2",
          nestingLevel === 0 && "shadow-sm",
          nestingLevel === 1 && "shadow-sm",
          isSelected && "ring-1 ring-blue-500/80",
          isActive && "ring-2 ring-blue-600"
        )}
        style={currentStyle}
      >
        <li
          onClick={handleSelectNode}
          className={cn(
            "flex items-center space-x-1 rounded-md p-1.5 transition-all duration-200 cursor-pointer ",
            "hover:bg-black/5"
          )}
        >
          {hasChildren && (
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
          )}
          <DynamicIcon
            iconName={getIcons(node.node_type)}
            className={cn("h-4 w-4 flex-shrink-0")}
            color={nodeStyle.iconColor}
          />
          <span
            className={cn(
              "flex-1 text-sm truncate",
              isSelected ? "font-semibold" : "font-medium"
            )}
          >
            {node.name}
          </span>
        </li>
        {hasChildren && (
          <CollapsibleContent>
            <ul className="pl-2 pt-1 space-y-1">
              {node.children?.map((child) => (
                <TreeNode
                  key={child.key}
                  node={child}
                  nestingLevel={nestingLevel + 1}
                />
              ))}
            </ul>
          </CollapsibleContent>
        )}
      </div>
    </Collapsible>
  );
};

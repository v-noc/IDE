import React from "react";
import type { ProjectNode } from "@/types/project";
import useProjectStore from "@/stores/useProjectStore";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { DynamicIcon } from "@/components/ui/DynamicIcon";

interface TreeNodeProps {
  node: ProjectNode;
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

  const isOpen = expandedNodeIds.has(node.id);

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    toggleNodeExpansion(node.id);
  };

  const isSelected = selectedNode?.id === node.id;
  const isActive = activeNodeId === node.id;
  const hasChildren = node.children && node.children.length > 0;

  const handleSelectNode = () => {
    setSelectedNode(node);
  };

  const defaultBackgroundColor = "rgba(241, 245, 249, 0.5)"; // slate-100 with 50% opacity
  const defaultTextColor = "#475569"; // slate-600
  const defaultBorderColor = "rgba(226, 232, 240, 0.8)"; // slate-200 with 80% opacity

  const hoverBackgroundColor = "rgba(241, 245, 249, 1)"; // slate-100

  const cardColorWithOpacity = (color: string, opacity: number) => {
    const hex = color.replace("#", "");
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  };

  const baseStyle = {
    backgroundColor: node.cardColor
      ? cardColorWithOpacity(node.cardColor, 0.2)
      : defaultBackgroundColor,
    color: node.textColor || defaultTextColor,
    borderColor: node.cardColor
      ? cardColorWithOpacity(node.cardColor, 0.5)
      : defaultBorderColor,
  };

  const selectedStyle = {
    backgroundColor: node.cardColor
      ? cardColorWithOpacity(node.cardColor, 0.4)
      : hoverBackgroundColor,
    color: node.textColor || defaultTextColor,
    borderColor: node.cardColor || "#3b82f6",
  };

  const activeStyle = {
    backgroundColor: node.cardColor
      ? cardColorWithOpacity(node.cardColor, 0.5)
      : hoverBackgroundColor,
    color: node.textColor || defaultTextColor,
    borderColor: node.cardColor
      ? cardColorWithOpacity(node.cardColor, 0.9)
      : "#2563eb",
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
          nestingLevel === 0 && "shadow-md",
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
            iconName={node.icon}
            className={cn("h-4 w-4 flex-shrink-0")}
            color={node.iconColor || currentStyle.color}
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
                  key={child.id}
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

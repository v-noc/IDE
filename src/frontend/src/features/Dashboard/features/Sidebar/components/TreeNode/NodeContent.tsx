import React from "react";
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
import { TreeNode } from ".";

interface NodeContentProps {
  node: ProjectTreeResponse;
  isOpen: boolean;
  isSelected: boolean;
  isActive: boolean;
  hasChildren: boolean;
  nestingLevel: number;
  handleToggle: (e: React.MouseEvent) => void;
  handleSelectNode: () => void;
}

export const NodeContent = ({
  node,
  isOpen,
  isSelected,
  isActive,
  hasChildren,
  nestingLevel,
  handleToggle,
  handleSelectNode,
}: NodeContentProps) => {
  const nodeStyle = getNodeStyle(node);

  const currentStyle = {
    backgroundColor: nodeStyle.backgroundColor,
    color: nodeStyle.color,
    borderColor: nodeStyle.borderColor,
  };

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

import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import { useTreeNode } from "./useTreeNode";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";

interface TreeNodeProps {
  node: ProjectTreeResponse;
  nestingLevel?: number;
}

export const TreeNode = ({ node, nestingLevel = 0 }: TreeNodeProps) => {
  const {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleRemove,
  } = useTreeNode(node);

  return (
    <NodeContextMenu
      onFocus={handleFocus}
      onExpand={handleExpand}
      onRemove={handleRemove}
    >
      <NodeContent
        node={node}
        isOpen={isOpen}
        isSelected={isSelected}
        isActive={isActive}
        hasChildren={hasChildren}
        nestingLevel={nestingLevel}
        handleToggle={handleToggle}
        handleSelectNode={handleSelectNode}
      />
    </NodeContextMenu>
  );
};
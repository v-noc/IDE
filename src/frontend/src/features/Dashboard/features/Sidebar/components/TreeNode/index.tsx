import { type ContainerNodeTree } from "@/types/project";
import { NodeContextMenu } from "./NodeContextMenu";
import { NodeContent } from "./NodeContent";
import type { AnyNodeTree, CallNodeTree } from "@/types/project";
import { useTreeNodeState } from "../../hooks/useTreeNodeState";
import { useTreeNodeHandlers } from "../../hooks/useTreeNodeHandlers";
import { useTreeNodeActions } from "../../hooks/useTreeNodeAction";

interface TreeNodeProps {
  node: ContainerNodeTree;
  nestingLevel?: number;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const TreeNode = ({
  node,
  nestingLevel = 0,
  childFilter,
  onSelect,
}: TreeNodeProps) => {
  const {
    isOpen,
    isSelected,
    isActive,
    hasChildren
  } = useTreeNodeState(node, childFilter);

  const {
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleContextAction
  } = useTreeNodeHandlers(node);

  const { handleRemoveCall, handleDeleteGroup } = useTreeNodeActions(node);

  if (!node) return null;

  const handleSelectOverride = onSelect
    ? () => onSelect(node)
    : handleSelectNode;

  const onAction = (action: string) => {
    if (action === "remove-call") {
      handleRemoveCall(node as unknown as CallNodeTree);
      return;
    }
    if (action === "delete-group") {
      handleDeleteGroup();
      return;
    }
    if (action === "focus") {
      handleFocus();
      return;
    }
    if (action === "expand") {
      handleExpand();
      return;
    }
    // All other actions (add-call, create-group, manage-group, prompt-builder) 
    // are handled by the handlers hook which opens the global modal store
    handleContextAction(action);
  };

  return (
    <NodeContextMenu
      node={node as AnyNodeTree}
      onAction={onAction}
    >
      <NodeContent
        node={node}
        isOpen={isOpen}
        isSelected={isSelected}
        isActive={isActive}
        hasChildren={hasChildren}
        nestingLevel={nestingLevel}
        handleToggle={handleToggle}
        handleSelectNode={handleSelectOverride}
        childFilter={childFilter}
        onSelect={onSelect}
      />
    </NodeContextMenu>
  );
};

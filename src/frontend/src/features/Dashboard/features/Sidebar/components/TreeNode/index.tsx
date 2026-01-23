import { type ContainerNodeTree } from "@/types/project";
import { NodeContextMenu } from "@/features/Dashboard/components/NodeContextMenu";
import { NodeContent } from "./NodeContent";
import { useTreeNodeState } from "../../hooks/useTreeNodeState";
import { useNodeHandlers } from "@/features/Dashboard/hooks/useNodeHandlers";

interface TreeNodeProps {
  node: ContainerNodeTree;
  tabId: string;
  nestingLevel?: number;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const TreeNode = ({
  node,
  tabId,
  nestingLevel = 0,
  childFilter,
  onSelect,
}: TreeNodeProps) => {
  const { isOpen, isSelected, isActive, hasChildren } = useTreeNodeState(
    node,
    childFilter,
    tabId
  );

  const {
    handleToggle,
    handleSelectNode,
    onAction
  } = useNodeHandlers(node._key, tabId);



  if (!node) return null;

  const handleSelectOverride = onSelect
    ? () => onSelect(node)
    : handleSelectNode;



  return (
    <NodeContextMenu
      nodeId={node._key}
      nodeType={node.node_type}
      manuallyCreated={(node as any).manually_created}
      onAction={onAction}
    >
      <NodeContent
        node={node}
        tabId={tabId}
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

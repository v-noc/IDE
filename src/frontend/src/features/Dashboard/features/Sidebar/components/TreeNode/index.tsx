import { useMemo } from "react";
import { type CallNodeTree, type ContainerNodeTree } from "@/types/project";
import { NodeContextMenu } from "@/features/Dashboard/components/NodeContextMenu";
import { NodeContent } from "./NodeContent";
import { useTreeNodeState } from "../../hooks/useTreeNodeState";
import { useNodeHandlers } from "@/features/Dashboard/hooks/useNodeHandlers";
import { useLazyCodeChildren } from "@/features/Dashboard/service/codeDescendants";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

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
  const isOpen = useProjectStore((s) =>
    (s.expandedNodeIds[tabId] ?? []).includes(node.id),
  );

  const lazy = useLazyCodeChildren(node, isOpen);

  const displayNode = useMemo((): ContainerNodeTree => {
    const base = node.children ?? [];
    const extra = lazy.loadedNodes;
    if (!extra.length) return node;
    return {
      ...node,
      children: [...base, ...extra],
    };
  }, [node, lazy.loadedNodes]);

  const lazyMeta = useMemo(
    () => ({ lazyHintCount: node.lazy_child_ids?.length ?? 0 }),
    [node.lazy_child_ids],
  );

  const { isSelected, isActive, hasChildren } = useTreeNodeState(
    displayNode,
    childFilter,
    tabId,
    lazyMeta,
  );

  const { handleToggle, handleSelectNode, onAction } = useNodeHandlers(
    node.id,
    tabId,
  );

  if (!node) return null;

  const handleSelectOverride = onSelect
    ? () => onSelect(node)
    : handleSelectNode;

  return (
    <NodeContextMenu
      nodeId={node.id}
      nodeType={node.node_type}
      manuallyCreated={
        node.node_type === "call"
          ? (node as CallNodeTree).manually_created
          : undefined
      }
      onAction={onAction}
    >
      <NodeContent
        node={displayNode}
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

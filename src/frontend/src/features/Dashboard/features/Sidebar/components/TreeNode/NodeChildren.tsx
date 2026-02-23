import { memo, useMemo } from "react";
import { TreeNode } from ".";
import { sortNodeChildren } from "@/features/Dashboard/utils/sortChildren";
import type { ContainerNodeTree } from "@/types/project";

interface NodeChildrenProps {
  node: ContainerNodeTree;
  tabId: string;
  nestingLevel: number;
  childFilter?: (node: ContainerNodeTree) => boolean;
  onSelect?: (node: ContainerNodeTree) => void;
}

export const NodeChildren = memo(function NodeChildren({
  node,
  tabId,
  nestingLevel,
  childFilter,
  onSelect,
}: NodeChildrenProps) {
  const sortedChildren = useMemo(() => {
    const filtered = (node.children ?? []).filter((n) =>
      childFilter ? childFilter(n as ContainerNodeTree) : true,
    );
    return sortNodeChildren(filtered as ContainerNodeTree[], node.node_type);
  }, [node.children, node.node_type, childFilter]);

  if (sortedChildren.length === 0) return null;

  return (
    <ul className="pl-2 pt-1 space-y-1">
      {sortedChildren.map((child) => (
        <TreeNode
          key={child.id}
          node={child}
          tabId={tabId}
          nestingLevel={nestingLevel + 1}
          childFilter={childFilter}
          onSelect={onSelect}
        />
      ))}
    </ul>
  );
});

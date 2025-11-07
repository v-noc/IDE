import React, { useMemo } from "react";
import type { AnyNodeTree, ContainerNodeTree } from "@/types/project";
import { TreeView, type TreeDataItem } from "@/components/ui/tree-view";
import { Checkbox } from "@/components/ui/checkbox";

interface TreePaneProps {
  root: ContainerNodeTree;
  checked: Record<string, boolean>;
  expanded: Record<string, boolean>;
  selectedNodeKey: string | null;
  onToggleChecked: (key: string) => void;
  onToggleExpanded: (key: string) => void;
  onSelect: (key: string) => void;
}

const nodeToTreeItem = (
  node: AnyNodeTree,
  checked: Record<string, boolean>,
  onToggleChecked: (key: string) => void
): TreeDataItem => {
  return {
    id: node._key,
    name: node.name,
    subtitle: node.description ? node.description.substring(0, 50) : undefined,
    children: (node.children ?? []).map((c) =>
      nodeToTreeItem(c as AnyNodeTree, checked, onToggleChecked)
    ),
    actions: (
      <Checkbox
        checked={!!checked[node._key]}
        onCheckedChange={() => {
          onToggleChecked(node._key);
        }}
        onClick={(e) => e.stopPropagation()}
      />
    ),
  };
};

export const TreePane: React.FC<TreePaneProps> = ({
  root,
  checked,
  selectedNodeKey,
  onToggleChecked,
  onSelect,
}) => {
  const treeData = useMemo(
    () => nodeToTreeItem(root as AnyNodeTree, checked, onToggleChecked),
    [root, checked, onToggleChecked]
  );

  return (
    <TreeView
      data={treeData}
      initialSelectedItemId={selectedNodeKey ?? root._key}
      onSelectChange={(item) => item && onSelect(item.id)}
      expandAll={false}
      className="h-full overflow-y-auto"
    />
  );
};

export default TreePane;

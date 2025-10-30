import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import type { AnyNodeTree, NodeType } from "@/types/project";
import { TreeView, type TreeDataItem } from "@/components/ui/tree-view";
import { DynamicIcon } from "@/components/DynamicIcon";
import getIcons from "@/features/Dashboard/utils/getIcons";

interface SelectNodeDialogProps {
  isOpen?: boolean;
  onClose?: () => void;
  list: AnyNodeTree[];
  selectNodeType: NodeType[];
  onSelect: (node: AnyNodeTree) => void;
}
const SelectNodeDialog = ({
  isOpen,
  onClose,
  list,
  selectNodeType,
  onSelect,
}: SelectNodeDialogProps) => {
  const [selectedNode, setSelectedNode] = useState<AnyNodeTree | null>(null);
  const toTreeDataItem = React.useCallback(
    (node: AnyNodeTree): TreeDataItem => {
      const rawChildren = (node as unknown as Record<string, unknown>)
        .children as unknown;
      const children = Array.isArray(rawChildren)
        ? (rawChildren as unknown[])
            .filter(
              (child: unknown) => (child as AnyNodeTree).node_type !== "call"
            )
            .map((child) => toTreeDataItem(child as AnyNodeTree))
        : undefined;

      const IconComp = () => (
        <DynamicIcon
          iconName={getIcons(node.node_type)}
          className="h-4 w-4 shrink-0 mr-2"
        />
      );

      return {
        id: node._key,
        name: `${node.name} (${node.node_type})`,
        icon: IconComp,
        children,
        onClick: () => {
          if (selectNodeType.includes(node.node_type)) {
            setSelectedNode(node);
          }
        },
      };
    },
    [selectNodeType]
  );

  const treeData = React.useMemo<TreeDataItem[]>(
    () => list.filter((node) => node.node_type !== "call").map(toTreeDataItem),
    [list, toTreeDataItem]
  );

  const handleSubmit = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (selectedNode) {
      onSelect(selectedNode);
    }
    onClose?.();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Select {selectNodeType.join(", ")}</DialogTitle>
        </DialogHeader>
        <div className="mt-2 max-h-72 overflow-auto rounded-md border p-1">
          <TreeView data={treeData} className="text-sm" />
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          {selectedNode
            ? `Selected: ${selectedNode.name} (${selectedNode.node_type})`
            : `Pick a ${selectNodeType.join(" or ")} from the list.`}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!selectedNode} type="submit" onClick={handleSubmit}>
            Submit
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SelectNodeDialog;

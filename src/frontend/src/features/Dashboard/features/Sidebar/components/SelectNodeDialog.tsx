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

      return {
        id: node._key,
        name: node.name,
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
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Select {selectNodeType.join(", ")}</DialogTitle>
        </DialogHeader>
        <div className="mt-2 max-h-72 overflow-auto rounded-md border p-1">
          <TreeView data={treeData} className="text-sm" />
        </div>
        <DialogFooter>
          <Button disabled={!selectedNode} type="submit" onClick={handleSubmit}>
            submit
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default SelectNodeDialog;

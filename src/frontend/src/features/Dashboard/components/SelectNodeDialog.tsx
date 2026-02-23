import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { pipe, filter as rFilter, map as rMap } from "remeda";

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
  const [query, setQuery] = useState("");

  function useDebouncedValue<T>(value: T, delayMs: number) {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
      const id = setTimeout(() => setDebounced(value), delayMs);
      return () => clearTimeout(id);
    }, [value, delayMs]);
    return debounced;
  }

  const debouncedQuery = useDebouncedValue(query, 250);

  const toTreeDataItem = useCallback(
    (node: AnyNodeTree): TreeDataItem => {
      const rawChildren = (node as unknown as Record<string, unknown>)
        .children as unknown;
      const children = Array.isArray(rawChildren)
        ? (rawChildren as unknown[])
            .filter(
              (child: unknown) => (child as AnyNodeTree).node_type !== "call",
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
        id: node.id,
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
    [selectNodeType],
  );

  const treeData = useMemo<TreeDataItem[]>(() => {
    const q = debouncedQuery.trim();

    // No search: render hierarchical tree (excluding calls as before)
    if (q.length === 0) {
      return pipe(
        list,
        rFilter((n: AnyNodeTree) => n.node_type !== "call"),
        rMap(toTreeDataItem),
      );
    }

    // With search: flatten all descendants and filter by name, show as leaves with path text
    const queryLc = q.toLowerCase();

    type FlatRecord = { node: AnyNodeTree; parents: string[] };

    const flattenAll = (
      nodes: AnyNodeTree[],
      parents: string[] = [],
    ): FlatRecord[] =>
      nodes.flatMap((n) => {
        // Exclude call nodes and their subtrees
        if (n.node_type === "call") return [];
        const children = (n as unknown as { children?: AnyNodeTree[] })
          .children;
        const nextParents = [...parents, n.name];
        const self: FlatRecord = { node: n, parents };
        const childRecords = Array.isArray(children)
          ? flattenAll(children, nextParents)
          : [];
        return [self, ...childRecords];
      });

    const flat = flattenAll(list);
    const matches = flat.filter(
      (r) =>
        r.node.node_type !== "call" &&
        r.node.name.toLowerCase().includes(queryLc),
    );

    return matches.map((r) => {
      const IconComp = () => (
        <DynamicIcon
          iconName={getIcons(r.node.node_type)}
          className="h-4 w-4 shrink-0 mr-2"
        />
      );
      const parentsTail = r.parents.slice(-2);
      const pathText = parentsTail.join(" / ");
      return {
        id: r.node.id,
        name: `${r.node.name} (${r.node.node_type})`,
        subtitle: pathText,
        icon: IconComp,
        onClick: () => {
          if (selectNodeType.includes(r.node.node_type)) {
            setSelectedNode(r.node);
          }
        },
      } as TreeDataItem;
    });
  }, [list, toTreeDataItem, debouncedQuery, selectNodeType]);

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
        <div className="mt-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name..."
          />
        </div>
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

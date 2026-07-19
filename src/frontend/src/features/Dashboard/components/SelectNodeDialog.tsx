import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useQueries, useQueryClient } from "@tanstack/react-query";
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
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import {
  canLazyLoadCodeChildren,
  getCodeDescendantsQueryOptions,
} from "@/features/Dashboard/service/codeDescendants";
import { mergeStructureAndLazyChildren } from "@/features/Dashboard/utils/mergeCodeTreeChildren";
import queryKeys from "@/lib/queryKeys";

interface SelectNodeDialogProps {
  isOpen?: boolean;
  onClose?: () => void;
  list: AnyNodeTree[];
  selectNodeType: NodeType[];
  onSelect: (node: AnyNodeTree) => void;
}

function useDebouncedValue<T>(value: T, delayMs: number) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);
  return debounced;
}

function getNodeChildren(node: AnyNodeTree): AnyNodeTree[] | undefined {
  return (node as { children?: AnyNodeTree[] }).children;
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
  const [expandedIds, setExpandedIds] = useState<string[]>([]);

  const queryClient = useQueryClient();
  const projectId = useProjectStore((s) => s.projectData?.id ?? "");
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const debouncedQuery = useDebouncedValue(query, 250);

  useEffect(() => {
    if (isOpen) {
      setSelectedNode(null);
      setQuery("");
      setExpandedIds([]);
    }
  }, [isOpen]);

  const handleExpandedChange = useCallback((itemId: string, expanded: boolean) => {
    setExpandedIds((prev) => {
      if (expanded) {
        return prev.includes(itemId) ? prev : [...prev, itemId];
      }
      return prev.filter((id) => id !== itemId);
    });
  }, []);

  const descendantQueries = useQueries({
    queries: expandedIds.map((parentId) => ({
      ...getCodeDescendantsQueryOptions(
        projectId,
        parentId,
        branch,
        ref,
        compareTo,
      ),
      enabled: Boolean(projectId) && Boolean(isOpen),
    })),
  });

  const descendantsDataKey = descendantQueries
    .map((q) => q.dataUpdatedAt)
    .join("|");

  const lazyChildrenByParentId = useMemo(() => {
    const m = new Map<string, AnyNodeTree[]>();
    expandedIds.forEach((parentId, i) => {
      const roots = descendantQueries[i]?.data?.children;
      if (roots?.length) {
        m.set(parentId, roots as unknown as AnyNodeTree[]);
      }
    });
    return m;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expandedIds, descendantsDataKey]);

  const getCachedLazyChildren = useCallback(
    (nodeId: string): AnyNodeTree[] | undefined => {
      const cached = queryClient.getQueryData<{
        children?: AnyNodeTree[];
      }>(
        queryKeys.code.descendants(
          projectId,
          nodeId,
          branch,
          ref,
          compareTo,
        ),
      );
      const children = cached?.children;
      return children?.length
        ? (children as unknown as AnyNodeTree[])
        : undefined;
    },
    [queryClient, projectId, branch, ref, compareTo],
  );

  const getMergedChildren = useCallback(
    (node: AnyNodeTree, includeCached: boolean): AnyNodeTree[] => {
      const lazyLoaded =
        lazyChildrenByParentId.get(node.id) ??
        (includeCached ? getCachedLazyChildren(node.id) : undefined);
      return mergeStructureAndLazyChildren(
        getNodeChildren(node),
        lazyLoaded,
      ).filter((child) => child.node_type !== "call");
    },
    [lazyChildrenByParentId, getCachedLazyChildren],
  );

  const toTreeDataItem = useCallback(
    (node: AnyNodeTree): TreeDataItem => {
      const mergedChildren = getMergedChildren(node, false);
      const hasLazyHint = canLazyLoadCodeChildren(node);
      const hasChildren = mergedChildren.length > 0 || hasLazyHint;

      const IconComp = () => (
        <DynamicIcon
          iconName={getIcons(node.node_type)}
          className="h-4 w-4 shrink-0 mr-2"
        />
      );

      const childItems = hasChildren
        ? mergedChildren.length > 0
          ? mergedChildren.map((child) => toTreeDataItem(child))
          : []
        : undefined;

      return {
        id: node.id,
        name: `${node.name} (${node.node_type})`,
        icon: IconComp,
        children: childItems,
        onClick: () => {
          if (selectNodeType.includes(node.node_type)) {
            setSelectedNode(node);
          }
        },
      };
    },
    [getMergedChildren, selectNodeType],
  );

  const treeData = useMemo<TreeDataItem[]>(() => {
    const q = debouncedQuery.trim();

    if (q.length === 0) {
      return pipe(
        list,
        rFilter((n: AnyNodeTree) => n.node_type !== "call"),
        rMap(toTreeDataItem),
      );
    }

    const queryLc = q.toLowerCase();

    type FlatRecord = { node: AnyNodeTree; parents: string[] };

    const flattenAll = (
      nodes: AnyNodeTree[],
      parents: string[] = [],
    ): FlatRecord[] =>
      nodes.flatMap((n) => {
        if (n.node_type === "call") return [];
        const children = getMergedChildren(n, true);
        const nextParents = [...parents, n.name];
        const self: FlatRecord = { node: n, parents };
        const childRecords =
          children.length > 0 ? flattenAll(children, nextParents) : [];
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
  }, [list, toTreeDataItem, debouncedQuery, selectNodeType, getMergedChildren]);

  const handleSubmit = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    if (selectedNode) {
      onSelect(selectedNode);
    }
    onClose?.();
  };

  const isLoadingChildren = descendantQueries.some((q) => q.isFetching);

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
          <TreeView
            data={treeData}
            className="text-sm"
            onExpandedChange={handleExpandedChange}
          />
          {isLoadingChildren && (
            <p className="px-2 py-1 text-xs text-muted-foreground">
              Loading…
            </p>
          )}
        </div>
        <div className="mt-2 text-xs text-muted-foreground">
          {selectedNode
            ? `Selected: ${selectedNode.name} (${selectedNode.node_type})`
            : `Expand files to browse functions and classes, or search by name.`}
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

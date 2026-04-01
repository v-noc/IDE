import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { ContainerNodeTree } from '@/types/project';
import { useShallow } from 'zustand/react/shallow';

export type TreeNodeLazyMeta = {
  /** From API lazy_child_ids — children exist but not in structure payload. */
  lazyHintCount: number;
};

/**
 * Core tree node state - selection, expansion, children.
 * Pure derived state, no side effects.
 */
export function useTreeNodeState(
  node: ContainerNodeTree,
  childFilter: (node: ContainerNodeTree) => boolean = () => true,
  tabId: string,
  lazyMeta?: TreeNodeLazyMeta | null,
) {
  // Selective subscriptions - only re-render when these change
  const selectedNodeKey = useProjectStore((s) => s.selectedNode[tabId]?.id);
  const secondarySelectedKey = useProjectStore((s) => s.secondarySelectedNode[tabId]?.id);
  const activeNodeId = useProjectStore((s) => s.activeNodeId[tabId]);
  const expandedNodeIds = useProjectStore(useShallow((s) => s.expandedNodeIds[tabId] ?? []));

  const isOpen = node ? expandedNodeIds.includes(node.id) : false;
  const isSelected = node ? (selectedNodeKey === node.id || secondarySelectedKey === node.id) : false;
  const isActive = node ? activeNodeId === node.id : false;

  const hasChildren = useMemo(() => {
    if (!node) return false;
    const children = node.children ?? [];
    if (children.some((child) => childFilter(child as ContainerNodeTree))) {
      return true;
    }
    if (lazyMeta && lazyMeta.lazyHintCount > 0) return true;
    return false;
  }, [node, childFilter, lazyMeta]);

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
  };
}

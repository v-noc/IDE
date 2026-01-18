import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { ContainerNodeTree } from '@/types/project';
import { useShallow } from 'zustand/react/shallow';

/**
 * Core tree node state - selection, expansion, children.
 * Pure derived state, no side effects.
 */
export function useTreeNodeState(
  node: ContainerNodeTree,
  childFilter: (node: ContainerNodeTree) => boolean = () => true,
  tabId: string
) {
  // Selective subscriptions - only re-render when these change
  const selectedNodeKey = useProjectStore((s) => s.selectedNode[tabId]?._key);
  const secondarySelectedKey = useProjectStore((s) => s.secondarySelectedNode[tabId]?._key);
  const activeNodeId = useProjectStore((s) => s.activeNodeId[tabId]);
  const expandedNodeIds = useProjectStore(useShallow((s) => s.expandedNodeIds[tabId] ?? []));

  const isOpen = node ? expandedNodeIds.includes(node._key) : false;
  const isSelected = node ? (selectedNodeKey === node._key || secondarySelectedKey === node._key) : false;
  const isActive = node ? activeNodeId === node._key : false;

  const hasChildren = useMemo(() => {
    if (!node) return false;
    const children = node.children ?? [];
    return children.some((child) => childFilter(child as ContainerNodeTree));
  }, [node, childFilter]);

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
  };
}

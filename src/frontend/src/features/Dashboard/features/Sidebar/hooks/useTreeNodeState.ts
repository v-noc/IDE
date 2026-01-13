import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import type { ContainerNodeTree } from '@/types/project';

/**
 * Core tree node state - selection, expansion, children.
 * Pure derived state, no side effects.
 */
export function useTreeNodeState(
  node: ContainerNodeTree,
  childFilter: (node: ContainerNodeTree) => boolean = () => true
) {
  // Selective subscriptions - only re-render when these change
  const selectedNodeKey = useProjectStore((s) => s.selectedNode?._key);
  const secondarySelectedKey = useProjectStore((s) => s.secondarySelectedNode?._key);
  const activeNodeId = useProjectStore((s) => s.activeNodeId);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);

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

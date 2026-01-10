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

  const isOpen = expandedNodeIds.includes(node._key);
  const isSelected = selectedNodeKey === node._key || secondarySelectedKey === node._key;
  const isActive = activeNodeId === node._key;

  const hasChildren = useMemo(() => {
    const children = node.children ?? [];
    return children.some((child) => childFilter(child as ContainerNodeTree));
  }, [node.children, childFilter]);

  return {
    isOpen,
    isSelected,
    isActive,
    hasChildren,
  };
}

import type { ContainerNodeTree } from '@/types/project';
import { useTreeNodeState } from './useTreeNodeState';
import { useTreeNodeHandlers } from './useTreeNodeHandlers';
import { useTreeNodeActions } from '@/features/Dashboard/features/Sidebar/hooks/useTreeNodeAction';

/**
 * Combined hook for backward compatibility.
 * Prefer using individual hooks for new code.
 */
export function useTreeNode(
  node: ContainerNodeTree,
  childFilter?: (node: ContainerNodeTree) => boolean
) {
  const state = useTreeNodeState(node, childFilter);
  const handlers = useTreeNodeHandlers(node);
  const actions = useTreeNodeActions(node);

  return {
    ...state,
    ...handlers,
    ...actions,
  };
}

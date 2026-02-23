import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { useAddCall, useRemoveCall } from '@/features/Dashboard/service/useCall';
import { useDeleteGroup } from '@/features/Dashboard/service/useGroup';
import type { AnyNodeTree, ContainerNodeTree, CallNodeTree } from '@/types/project';

/**
 * Mutation actions for tree nodes.
 * Only initialize mutations when needed.
 */
export function useTreeNodeActions(node: ContainerNodeTree) {
  const projectKey = useProjectStore((s) => s.projectData?.id ?? '');

  // Lazy initialization - only create mutations when called
  const addCall = useAddCall(node?.id ?? '', projectKey);
  const removeCall = useRemoveCall(projectKey);
  const deleteGroup = useDeleteGroup(node?.id ?? '', projectKey);

  const handleAddCall = useCallback((targetNode: AnyNodeTree) => {
    addCall.mutate({
      callee_target_id: targetNode.id,
      name: targetNode.name,
      description: targetNode.description,
    });
  }, [addCall]);

  const handleRemoveCall = useCallback((callNode: CallNodeTree) => {
    removeCall.mutate(callNode.id);
  }, [removeCall]);

  const handleDeleteGroup = useCallback(() => {
    if (!node || node.node_type !== 'group') return;
    deleteGroup.mutate();
  }, [node, deleteGroup]);

  return {
    handleAddCall,
    handleRemoveCall,
    handleDeleteGroup,
    isAddingCall: addCall.isPending,
    isRemovingCall: removeCall.isPending,
    isDeletingGroup: deleteGroup.isPending,
  };
}

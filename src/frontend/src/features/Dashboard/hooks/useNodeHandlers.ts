import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import useTabStore from '@/features/Dashboard/store/useTabStore';
import { useSidebarModalStore } from '@/features/Dashboard/store/useSidebarModalStore';
import type { AnyNodeTree, CallNodeTree, ContainerNodeTree } from '@/types/project';
import { useShallow } from 'zustand/react/shallow';
import { useTreeNodeActions } from './useNodeAction';
import { findNodeByKey } from '@/features/Dashboard/utils/findNode';
import type { ProjectStore } from '@/features/Dashboard/store/useProjectStore';

/**
 * Event handlers for tree node interactions.
 * All mutations dispatch to modal store or API.
 */
export function useNodeHandlers(nodeId: string, tabId: string) {
  // Store actions
  const handleNodeSelection = useTabStore((s: any) => s.handleNodeSelection);
  const setSecondarySelectedNode = useProjectStore((s: any) => s.setSecondarySelectedNode);
  const secondarySelectedNode = useProjectStore((s: any) => s.secondarySelectedNode[tabId]);
  const selectedNode = useProjectStore((s: any) => s.selectedNode[tabId]);
  const toggleNodeExpansion = useProjectStore((s: any) => s.toggleNodeExpansion);
  const pushFocus = useProjectStore((s: any) => s.pushFocus);
  const focusStack = useProjectStore(useShallow((s: ProjectStore) => s.focusStack[tabId] ?? []));

  // Helper to get fresh node from store for actions that need full object
  const getNode = useCallback(() => {
    const projectData = useProjectStore.getState().projectData;
    if (!projectData) return null;
    return findNodeByKey(projectData, nodeId);
  }, [nodeId]);

  const node = getNode();
  const { handleRemoveCall, handleDeleteGroup } = useTreeNodeActions(node as ContainerNodeTree);

  // Modal store
  const openModal = useSidebarModalStore((s: any) => s.openModal);

  // Toggle expansion
  const handleToggle = useCallback((e: React.MouseEvent) => {
    if (!nodeId) return;
    e.stopPropagation();
    toggleNodeExpansion(tabId, nodeId);
  }, [nodeId, tabId, toggleNodeExpansion]);

  // Select node
  const handleSelectNode = useCallback(() => {
    if (!nodeId) return;
    if (secondarySelectedNode) {
      setSecondarySelectedNode(tabId, null);
    }
    if (selectedNode?.id === nodeId) return;

    const node = getNode();
    if (!node) return;
    handleNodeSelection(tabId, node as AnyNodeTree, "primary");
  }, [nodeId, tabId, selectedNode, secondarySelectedNode, handleNodeSelection, setSecondarySelectedNode, getNode]);

  // Focus (zoom into node)
  const handleFocus = useCallback(() => {
    if (!nodeId) return;
    const lastFocused = focusStack[focusStack.length - 1];
    if (lastFocused?.id === nodeId) return;

    const node = getNode();
    if (!node) return;
    pushFocus(tabId, node as AnyNodeTree);
  }, [nodeId, tabId, focusStack, pushFocus, getNode]);

  // Expand/collapse
  const handleExpand = useCallback(() => {
    if (!nodeId) return;
    toggleNodeExpansion(tabId, nodeId);
  }, [nodeId, tabId, toggleNodeExpansion]);

  // Context menu actions - dispatch to modal store
  const handleContextAction = useCallback((action: string) => {
    const node = getNode();
    if (!node) return;
    switch (action) {
      case 'create-group':
      case 'manage-group':
      case 'add-call':
      case 'prompt-builder':
      case 'edit-virtual':
        openModal(action as any, node as AnyNodeTree);
        break;
      case 'copy-path':
        navigator.clipboard.writeText((node as any).path ?? node.name);
        break;
    }
  }, [getNode, openModal]);


  const onAction = (action: string) => {
    if (action === "remove-call") {
      handleRemoveCall(node as unknown as CallNodeTree);
      return;
    }
    if (action === "delete-group") {
      handleDeleteGroup();
      return;
    }
    if (action === "focus") {
      handleFocus();
      return;
    }
    if (action === "expand") {
      handleExpand();
      return;
    }
    // All other actions (add-call, create-group, manage-group, prompt-builder)
    // are handled by the handlers hook which opens the global modal store
    handleContextAction(action);
  };

  return {
    handleContextAction,
    handleDeleteGroup,
    handleRemoveCall,
    handleSelectNode,
    handleToggle,
    handleExpand,
    handleFocus,
    onAction,
  };
}

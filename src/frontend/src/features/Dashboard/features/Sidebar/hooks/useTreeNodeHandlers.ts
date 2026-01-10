import { useCallback } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { useSidebarModalStore } from '@/features/Dashboard/store/useSidebarModalStore';
import type { AnyNodeTree, ContainerNodeTree } from '@/types/project';

/**
 * Event handlers for tree node interactions.
 * All mutations dispatch to modal store or API.
 */
export function useTreeNodeHandlers(node: ContainerNodeTree) {
  // Store actions
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);
  const setSecondarySelectedNode = useProjectStore((s) => s.setSecondarySelectedNode);
  const secondarySelectedNode = useProjectStore((s) => s.secondarySelectedNode);
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);
  const pushFocus = useProjectStore((s) => s.pushFocus);
  const focusStack = useProjectStore((s) => s.focusStack);

  // Modal store
  const openModal = useSidebarModalStore((s) => s.openModal);

  // Toggle expansion
  const handleToggle = useCallback((e: React.MouseEvent) => {
    if (!node) return;
    e.stopPropagation();
    toggleNodeExpansion(node._key);
  }, [node, toggleNodeExpansion]);

  // Select node
  const handleSelectNode = useCallback(() => {
    if (!node) return;
    if (secondarySelectedNode) {
      setSecondarySelectedNode(null);
    }
    if (selectedNode?._key === node._key) return;
    setSelectedNode(node as AnyNodeTree);
  }, [node, selectedNode, secondarySelectedNode, setSelectedNode, setSecondarySelectedNode]);

  // Focus (zoom into node)
  const handleFocus = useCallback(() => {
    if (!node) return;
    const lastFocused = focusStack[focusStack.length - 1];
    if (lastFocused?._key === node._key) return;
    pushFocus(node as AnyNodeTree);
  }, [node, focusStack, pushFocus]);

  // Expand/collapse
  const handleExpand = useCallback(() => {
    if (!node) return;
    toggleNodeExpansion(node._key);
  }, [node, toggleNodeExpansion]);

  // Context menu actions - dispatch to modal store
  const handleContextAction = useCallback((action: string) => {
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
  }, [node, openModal]);

  return {
    handleToggle,
    handleSelectNode,
    handleFocus,
    handleExpand,
    handleContextAction,
  };
}

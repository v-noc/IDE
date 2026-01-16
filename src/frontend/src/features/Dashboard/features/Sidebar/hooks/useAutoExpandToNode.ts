import { useEffect, useEffectEvent, useRef } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { collectAncestorKeys } from '@/features/Dashboard/utils/treeUtils';
import type { AnyNodeTree, CallNodeTree } from '@/types/project';

/**
 * When a call node is selected, expand ancestors and scroll to target.
 * Uses refs instead of querySelector for proper React patterns.
 */
export function useAutoExpandToNode(projectTree: AnyNodeTree | null, tabId: string) {
  const selectedNode = useProjectStore((s) => s.selectedNode[tabId]);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);

  // Track the node to scroll to
  const scrollTargetRef = useRef<string | null>(null);

  /*
   * Handle auto-expansion logic.
   * Wrapped in useEffectEvent to avoid reactive loops with expandedNodeIds.
   */
  const handleAutoExpand = useEffectEvent((node: CallNodeTree) => {
    if (!projectTree) return;

    const target = node.target;
    const targetKey = target?._key;
    if (!targetKey) return;

    // Access current state directly to check before dispatching
    const currentExpanded = useProjectStore.getState().expandedNodeIds[tabId] ?? [];

    // Expand ancestors
    const ancestorKeys = collectAncestorKeys(projectTree, targetKey);
    for (const key of ancestorKeys) {
      if (!currentExpanded.includes(key)) {
        toggleNodeExpansion(tabId, key);
      }
    }

    scrollTargetRef.current = targetKey;
  });

  useEffect(() => {
    if (selectedNode && selectedNode.node_type === 'call' && projectTree) {
      handleAutoExpand(selectedNode as CallNodeTree);
    } else {
      scrollTargetRef.current = null;
    }
  }, [selectedNode, projectTree]); // Only rerun when selection actually changes

  // Scroll effect - runs after expansion
  useEffect(() => {
    if (!scrollTargetRef.current) return;

    // Use requestAnimationFrame to wait for DOM update
    requestAnimationFrame(() => {
      const el = document.querySelector(`[data-node-key="${scrollTargetRef.current}"]`);
      el?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      scrollTargetRef.current = null;
    });
  });

  return scrollTargetRef;
}

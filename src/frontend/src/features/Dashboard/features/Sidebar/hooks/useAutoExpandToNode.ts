import { useEffect, useRef } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { collectAncestorKeys } from '@/features/Dashboard/utils/treeUtils';
import type { AnyNodeTree, CallNodeTree } from '@/types/project';

/**
 * When a call node is selected, expand ancestors and scroll to target.
 * Uses refs instead of querySelector for proper React patterns.
 */
export function useAutoExpandToNode(projectTree: AnyNodeTree | null) {
  const selectedNode = useProjectStore((s) => s.selectedNode);
  const expandedNodeIds = useProjectStore((s) => s.expandedNodeIds);
  const toggleNodeExpansion = useProjectStore((s) => s.toggleNodeExpansion);

  // Track the node to scroll to
  const scrollTargetRef = useRef<string | null>(null);

  useEffect(() => {
    if (!selectedNode || selectedNode.node_type !== 'call' || !projectTree) {
      scrollTargetRef.current = null;
      return;
    }

    const target = (selectedNode as CallNodeTree).target;
    const targetKey = target?._key;
    if (!targetKey) return;

    // Expand ancestors
    const ancestorKeys = collectAncestorKeys(projectTree, targetKey);
    for (const key of ancestorKeys) {
      if (!expandedNodeIds.includes(key)) {
        toggleNodeExpansion(key);
      }
    }

    scrollTargetRef.current = targetKey;
  }, [selectedNode, projectTree, expandedNodeIds, toggleNodeExpansion]);

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

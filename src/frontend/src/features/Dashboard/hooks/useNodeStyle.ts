import { useMemo } from 'react';
import useProjectStore from '@/features/Dashboard/store/useProjectStore';
import { findNodeByKey } from '@/features/Dashboard/utils/findNode';
import getNodeStyle from '@/features/Dashboard/utils/getNodeStyle';
import type { ContainerNodeTree } from '@/types/project';

/**
 * Get styled properties for a node.
 * Resolves target for call nodes.
 */
export function useNodeStyle(node: ContainerNodeTree) {
  const projectData = useProjectStore((s) => s.projectData);

  return useMemo(() => {
    let effectiveNode = node;

    // For call nodes, use target's style
    if (node.target && projectData) {
      const targetNode = findNodeByKey(projectData, node.target.id);
      if (targetNode) {
        effectiveNode = targetNode;
      }
    }

    const style = getNodeStyle(effectiveNode);

    return {
      backgroundColor: style.cardColor,
      color: style.color,
      borderColor: style.borderColor,
      iconColor: style.iconColor,
    };
  }, [node, node.target, projectData]);
}

import type { AnyNodeTree, ContainerNodeTree } from '@/types/project';

/**
 * Collect ancestor keys path to a target key (for auto-expansion)
 */
export function collectAncestorKeys(root: AnyNodeTree, targetKey: string): string[] {
  const path: string[] = [];

  const dfs = (node: AnyNodeTree): boolean => {
    path.push(node._key);
    if (node._key === targetKey) return true;
    if (node.children) {
      for (const child of node.children as AnyNodeTree[]) {
        if (dfs(child)) return true;
      }
    }
    path.pop();
    return false;
  };

  dfs(root);
  path.pop(); // Remove target, keep only ancestors
  return path;
}

/**
 * Determines whether a child node should be rendered in the tree.
 * - Exclude "call" nodes
 * - Exclude "group" nodes with group_type === "call"
 */
export function shouldRenderChild(node: ContainerNodeTree): boolean {
  if (node.node_type === 'call') return false;

  if (node.node_type === 'group') {
    const groupType = (node as { group_type?: string }).group_type;
    return groupType !== 'call';
  }

  return true;
}

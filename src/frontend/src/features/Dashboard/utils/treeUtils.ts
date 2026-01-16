import type { AnyNodeTree, ContainerNodeTree, CallNodeTree } from '@/types/project';

export const findNodeByFunctionId = (
  root: AnyNodeTree,
  targetFunctionId: string
): AnyNodeTree | null => {
  // Check current node
  if (root._id === targetFunctionId) return root;

  // Check if it's a CallNode and its target matches
  if (
    root.node_type === "call" &&
    (root as CallNodeTree).target?._id === targetFunctionId
  ) {
    return root;
  }

  // Check children
  if (root.children) {
    for (const child of root.children) {
      const found = findNodeByFunctionId(child as AnyNodeTree, targetFunctionId);
      if (found) return found;
    }
  }
  return null;
};

export const findPathToNode = (
  root: AnyNodeTree,
  targetId: string,
  path: string[] = []
): string[] | null => {
  if (root._id === targetId) return path;
  if (root.children) {
    for (const child of root.children) {
      const result = findPathToNode(child as AnyNodeTree, targetId, [
        ...path,
        root._id,
      ]);
      if (result) return result;
    }
  }
  return null;
};

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

/**
 * Recursively find the parent of a node in the tree.
 */
export function getParentNode(
  node: AnyNodeTree,
  root: ContainerNodeTree
): ContainerNodeTree | null {
  if (root.children?.some((child) => child._key === node._key)) {
    return root;
  }
  for (const child of root.children ?? []) {
    const parent = getParentNode(node, child as ContainerNodeTree);
    if (parent) {
      return parent;
    }
  }

  return null;
}

/**
 * Find all siblings of a node.
 */
export function getSiblings(
  node: AnyNodeTree,
  root: ContainerNodeTree
): AnyNodeTree[] {
  const parentNode = getParentNode(node, root);
  if (!parentNode) return [];
  const children = parentNode.children ?? [];
  return children.filter((child) => child._key !== node._key) as AnyNodeTree[];
}

/**
 * Check if any Group node exists in tree
 */
export function containsGroup(node: AnyNodeTree): boolean {
  if (node.node_type === 'group') return true;
  const children = (node as { children?: AnyNodeTree[] }).children ?? [];
  return children.some(containsGroup);
}

/**
 * Flatten Group nodes by lifting their children
 */
export function flattenGroups(node: AnyNodeTree): AnyNodeTree[] {
  if (node.node_type === 'group') {
    const children = (node as { children?: AnyNodeTree[] }).children ?? [];
    return children.flatMap(flattenGroups);
  }

  const clone = { ...node } as AnyNodeTree;
  const children = (node as { children?: AnyNodeTree[] }).children ?? [];

  if (children.length > 0) {
    (clone as { children?: AnyNodeTree[] }).children = children.flatMap(flattenGroups);
  }

  return [clone];
}

/**
 * Extract short focus token from node key
 */
export function extractShortFocusToken(key: string): string {
  const uuidRegex = /([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})/;
  const match = key.match(uuidRegex);
  return match ? match[4] : key.slice(0, 6);
}

/**
 * Find node by focus token
 */
export function findNodeByFocusToken(
  root: AnyNodeTree,
  token: string
): AnyNodeTree | null {
  const stack: AnyNodeTree[] = [root];

  while (stack.length > 0) {
    const node = stack.pop()!;
    if (extractShortFocusToken(node._key) === token) return node;

    const children = (node as { children?: AnyNodeTree[] }).children ?? [];
    stack.push(...[...children].reverse());
  }

  return null;
}

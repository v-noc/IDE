import type { ContainerNodeTree } from '@/types/project';

/**
 * Sort children for folder/project views:
 * 1. Folders first
 * 2. Files second
 * 3. Other types last
 * 4. Alphabetically within each group
 */
export function sortNodeChildren(
  children: ContainerNodeTree[],
  parentType: string
): ContainerNodeTree[] {
  if (parentType !== 'folder' && parentType !== 'project') {
    return children;
  }

  const getRank = (node: ContainerNodeTree): number => {
    if (node.node_type === 'folder') return 0;
    if (node.node_type === 'file') return 1;
    return 2;
  };

  return [...children].sort((a, b) => {
    const rankDiff = getRank(a) - getRank(b);
    if (rankDiff !== 0) return rankDiff;
    return a.name.localeCompare(b.name);
  });
}

import { useMemo, useState } from "react";
import type { AnyNodeTree } from "@/types/project";

function filterTree(nodes: AnyNodeTree[], query: string): AnyNodeTree[] {
  if (!query.trim()) return nodes;

  const lowerQuery = query.toLowerCase();

  return nodes.reduce<AnyNodeTree[]>((acc, node) => {
    const nameMatch = node.name.toLowerCase().includes(lowerQuery);

    const children = 'children' in node ? node.children as AnyNodeTree[] : [];
    const filteredChildren = filterTree(children, query);

    if (nameMatch || filteredChildren.length > 0) {
      acc.push({
        ...node,
        children: filteredChildren,
      } as AnyNodeTree);
    }

    return acc;
  }, []);
}

export function useTreeFilter(nodes: AnyNodeTree[] | undefined) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredNodes = useMemo(() => {
    if (!nodes) return [];
    if (!searchQuery.trim()) return nodes;
    return filterTree(nodes, searchQuery);
  }, [nodes, searchQuery]);

  return {
    searchQuery,
    setSearchQuery,
    filteredNodes,
  };
}

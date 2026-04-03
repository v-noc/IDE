import type { AnyNodeTree } from "@/types/project";

/**
 * Structure children first, then lazy-loaded descendant roots; extras deduped by id.
 */
export function mergeStructureAndLazyChildren(
  structureChildren: AnyNodeTree[] | undefined,
  loadedNodes: AnyNodeTree[] | undefined,
): AnyNodeTree[] {
  const lazy = loadedNodes ?? [];
  const base = structureChildren ?? [];
  if (!lazy.length) {
    return base;
  }
  const seen = new Set(base.map((c) => c.id));
  const out = [...base];
  for (const n of lazy) {
    if (n?.id && !seen.has(n.id)) {
      seen.add(n.id);
      out.push(n);
    }
  }
  return out;
}

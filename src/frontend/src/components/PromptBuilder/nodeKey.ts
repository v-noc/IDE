import type { AnyNodeTree } from "@/types/project";

/** Stable id for prompt builder maps and tree rows (matches API `_key` when present). */
export function promptBuilderNodeKey(node: AnyNodeTree): string {
  const k = (node as { _key?: string })._key;
  return (typeof k === "string" && k) || node.id;
}

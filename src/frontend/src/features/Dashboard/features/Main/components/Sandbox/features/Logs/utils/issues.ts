import { type LogTreeNode } from "@/services/logs";

export interface IssueCounts {
  errors: number;
  warnings: number;
}

const cache = new WeakMap<LogTreeNode, IssueCounts>();

function level(node: LogTreeNode): string {
  return (node.level_name || "").toLowerCase();
}

function isError(node: LogTreeNode): boolean {
  return node.event_type === "error" || level(node) === "error" || !!node.error;
}

function isWarning(node: LogTreeNode): boolean {
  const l = level(node);
  return l === "warning" || l === "warn";
}

/**
 * Counts errors/warnings in a node's subtree, including the node itself.
 * A failed call is usually an `enter` node plus an `error` child describing the
 * same failure, so the node's own flag is skipped when such a child exists to
 * avoid counting one failure twice.
 */
export function countIssues(node: LogTreeNode): IssueCounts {
  const cached = cache.get(node);
  if (cached) return cached;

  const children = node.children ?? [];
  const hasErrorChild = children.some(isError);

  const counts: IssueCounts = {
    errors: isError(node) && !hasErrorChild ? 1 : 0,
    warnings: isWarning(node) ? 1 : 0,
  };
  for (const child of children) {
    const c = countIssues(child);
    counts.errors += c.errors;
    counts.warnings += c.warnings;
  }

  cache.set(node, counts);
  return counts;
}

/** Issues strictly below this node (what a collapsed row hides). */
export function countDescendantIssues(node: LogTreeNode): IssueCounts {
  const own = { errors: 0, warnings: 0 };
  for (const child of node.children ?? []) {
    const c = countIssues(child);
    own.errors += c.errors;
    own.warnings += c.warnings;
  }
  return own;
}

import { type LogTreeNode } from "@/services/logs";
import { type FlameGraphNode } from "@/components/FlameGraph/types";

/**
 * Converts a LogTreeNode (recursive execution log) into a FlameGraphNode.
 * It uses effective duration for values and extracts function names.
 */
export function mapLogToFlameNode(node: LogTreeNode): FlameGraphNode {
  // Determine duration: Use its own 'duration_ms' or its exit child's duration
  const exitChild = (node.children || []).find((c) => c.event_type === "exit");
  const duration = exitChild?.duration_ms

  // Filter children to remove technical 'exit'/'error' nodes that are 
  // already represented in the parent's data or as separate bars.
  // In a flame graph, we usually only care about the nested calls ('enter').
  const children = (node.children ?? [])
    .filter(c => c.event_type === 'enter')
    .map(mapLogToFlameNode);

  return {
    id: node._id || Math.random().toString(),
    name: node.message || "untitled",
    value: duration ?? 0,
    functionId: node.function_id || undefined,
    level_name: node.level_name || undefined,
    children: children.length > 0 ? children : [],
  };
}

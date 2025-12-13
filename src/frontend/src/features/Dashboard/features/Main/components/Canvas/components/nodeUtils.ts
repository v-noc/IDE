import type { AnyNodeTree } from "@/types/project";
import type { NodeMetadata } from "./EnhancedNode";

export const iconForType = (nodeType: AnyNodeTree["node_type"]): string => {
  switch (nodeType) {
    case "project":
      return "📦";
    case "folder":
      return "📁";
    case "file":
      return "📄";
    case "class":
      return "🏷️";
    case "function":
      return "ƒ";
    case "call":
      return "🔗";
    case "group":
      return "🗂️";
    default:
      return "📌";
  }
};

export interface SimpleTreeNode {
  _key: string;
  name: string;
  icon?: string;
  node_type: AnyNodeTree["node_type"];
  children?: AnyNodeTree[];
  target?: { _key: string };
  metadata?: Partial<NodeMetadata>;
  created_at?: string;
  updated_at?: string;
  description?: string;
}


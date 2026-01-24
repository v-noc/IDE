import type { AnyNodeTree } from "@/types/project";
import type { NodeMetadata } from "./nodes/EnhancedNode";


export interface SimpleTreeNode {
  _key: string;
  name: string;
  icon?: string;
  node_type: AnyNodeTree["node_type"];
  children?: AnyNodeTree[];
  target?: { _key: string, node_type: AnyNodeTree["node_type"], description?: string };
  metadata?: Partial<NodeMetadata>;
  created_at?: string;
  updated_at?: string;
  description?: string;
}


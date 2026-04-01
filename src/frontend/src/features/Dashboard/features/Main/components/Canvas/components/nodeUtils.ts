import type { AnyNodeTree } from "@/types/project";
import type { NodeMetadata } from "./nodes/EnhancedNode";


export interface SimpleTreeNode {
  id: string;
  name: string;
  icon?: string;
  node_type: AnyNodeTree["node_type"];
  children?: AnyNodeTree[];
  /** Backend lazy hints (structure shell); same as sidebar tree nodes. */
  lazy_child_ids?: string[];
  target?: { id: string, node_type: AnyNodeTree["node_type"], description?: string };
  metadata?: Partial<NodeMetadata>;
  created_at?: string;
  updated_at?: string;
  description?: string;
}


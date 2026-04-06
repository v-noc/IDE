import type { AnyNodeTree, GroupNodeTree } from "@/types/project";

export type GroupApiType = "structure_group" | "code_element_group" | "call_group";
export type GroupApiItemType =
  | "folder"
  | "file"
  | "structure_group"
  | "function"
  | "class"
  | "call"
  | "code_element_group"
  | "call_group";

const SCHEMA_PREFIX_TO_GROUP_API_TYPE: Record<string, GroupApiType> = {
  StructureGroupSchema: "structure_group",
  CodeElementGroupSchema: "code_element_group",
  CallGroupSchema: "call_group",
};

const API_GROUP_TYPES: GroupApiType[] = ["structure_group", "code_element_group", "call_group"];

export function mapFrontendGroupKindToApiType(
  groupKind?: GroupNodeTree["group_type"],
): GroupApiType | null {
  if (API_GROUP_TYPES.includes(groupKind as GroupApiType)) return groupKind as GroupApiType;
  if (groupKind === "folder_file") return "structure_group";
  if (groupKind === "code") return "code_element_group";
  if (groupKind === "call") return "call_group";
  return null;
}

function inferGroupApiTypeFromId(id: string): GroupApiType | null {
  const [schemaPrefix] = id.split("/");
  return schemaPrefix ? SCHEMA_PREFIX_TO_GROUP_API_TYPE[schemaPrefix] ?? null : null;
}

export function mapNodeToGroupApiType(node?: AnyNodeTree | null): GroupApiType | null {
  if (!node) return null;
  switch (node.node_type) {
    case "folder":
    case "file":
      return "structure_group";
    case "function":
    case "class":
      return "code_element_group";
    case "call":
      return "call_group";
    case "group": {
      const groupNode = node as GroupNodeTree;
      return mapFrontendGroupKindToApiType(groupNode.group_type) ?? inferGroupApiTypeFromId(node.id);
    }
    default:
      return null;
  }
}

/**
 * Whether a tree node may be added as a sibling into the "available" pool for a group of this API type
 * (aligns with StructureGroupSchema / CodeElementGroupSchema / CallGroupSchema child sets).
 */
export function isSiblingCandidateForGroupType(
  node: AnyNodeTree,
  groupType: GroupApiType,
): boolean {
  switch (groupType) {
    case "code_element_group":
      if (node.node_type === "function" || node.node_type === "class") return true;
      if (node.node_type === "group") {
        return mapNodeToGroupApiType(node) === "code_element_group";
      }
      return false;
    case "call_group":
      if (node.node_type === "call") return true;
      if (node.node_type === "group") {
        return mapNodeToGroupApiType(node) === "call_group";
      }
      return false;
    case "structure_group":
      if (node.node_type === "folder" || node.node_type === "file") return true;
      if (node.node_type === "group") {
        return mapNodeToGroupApiType(node) === "structure_group";
      }
      return false;
    default:
      return false;
  }
}

export function mapNodeToGroupItemType(node: AnyNodeTree): GroupApiItemType | null {
  switch (node.node_type) {
    case "folder":
      return "folder";
    case "file":
      return "file";
    case "function":
      return "function";
    case "class":
      return "class";
    case "call":
      return "call";
    case "group": {
      const groupApiType = mapNodeToGroupApiType(node);
      if (groupApiType === "structure_group") return "structure_group";
      if (groupApiType === "code_element_group") return "code_element_group";
      if (groupApiType === "call_group") return "call_group";
      return null;
    }
    default:
      return null;
  }
}

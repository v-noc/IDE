import type { NodeType } from "@/types/project";

/** Map Terminus schema @type / type string to sidebar node_type. */
export function schemaTypeToNodeType(schema: string): NodeType {
  if (schema.endsWith("ClassSchema")) return "class";
  if (schema.endsWith("FunctionSchema")) return "function";
  if (schema.endsWith("CallSchema")) return "call";
  if (schema.endsWith("CodeElementGroupSchema")) return "group";
  if (schema.endsWith("CallGroupSchema")) return "group";
  if (schema.endsWith("FileSchema")) return "file";
  if (schema.endsWith("FolderSchema")) return "folder";
  if (schema.endsWith("StructureGroupSchema")) return "group";
  return "group";
}

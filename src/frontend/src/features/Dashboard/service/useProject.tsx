import apiClient from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export type NodeType =
  | "folder"
  | "file"
  | "project"
  | "function"
  | "class"
  | "package";

// NodePosition type matching the Python backend
interface NodePosition {
  line_no: number;
  col_offset: number;
  end_line_no: number;
  end_col_offset: number;
}

// TypeKeyValuesProperties type matching the Python backend
interface TypeKeyValuesProperties {
  varname: string;
  varType: string;
  position: NodePosition;
}

// Properties types for each node type
interface ProjectProperties {
  path: string;
}

interface FolderProperties {
  path: string;
}

interface FileProperties {
  path: string;
}

interface FunctionProperties {
  position: NodePosition;
  inputs: TypeKeyValuesProperties[];
  outputs: TypeKeyValuesProperties[];
}

interface ClassProperties {
  position: NodePosition;
  fields: TypeKeyValuesProperties[];
}

interface PackageProperties {
  version?: string;
  source?: string;
  imported_paths: string[];
}

// Discriminated union for properties based on node type
type NodeProperties =
  | { type: "project"; properties: ProjectProperties }
  | { type: "folder"; properties: FolderProperties }
  | { type: "file"; properties: FileProperties }
  | { type: "function"; properties: FunctionProperties }
  | { type: "class"; properties: ClassProperties }
  | { type: "package"; properties: PackageProperties };

export interface ProjectTreeResponse {
  name: string;
  qname: string;
  key: string;
  node_type: NodeType;
  properties: NodeProperties["properties"];
  children: ProjectTreeResponse[];
}

const getProjectTreeWithKey = async (
  key: string
): Promise<ProjectTreeResponse> => {
  const response = await apiClient(`/project/${key}/tree`);
  return response as ProjectTreeResponse;
};

export const useGetProjectTreeWithKeyProject = ({ key }: { key: string }) => {
  return useQuery({
    queryKey: ["project", key],
    queryFn: () => getProjectTreeWithKey(key),
  });
};

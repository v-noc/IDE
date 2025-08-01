import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export interface ProjectTreeResponse {
  key: string;
  name: string;
  path: string;
  node_type: string;
  label: string;
  children: ProjectTreeResponse[];
  isVirtual?: boolean;
  parentId?: string | null;
}

export const useGetProjectTreeWithKeyProject = ({ key }: { key: string }) => {
  return useQuery({
    queryKey: ["projectTree", key],
    queryFn: () => getProjectTreeWithKey(key),
    enabled: !!key,
  });
};

const getProjectTreeWithKey = async (
  key: string
): Promise<ProjectTreeResponse> => {
  const response = await api(`/project/${key}/tree`);
  return response as ProjectTreeResponse;
};

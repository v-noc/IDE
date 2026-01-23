import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ProjectNodeTree } from "@/types/project";
import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";

const getProjectTreeWithKey = async (key: string): Promise<ProjectNodeTree> => {
  const response = await api(`${API_ROUTES.PROJECTS}${key}`);
  return response as ProjectNodeTree;
};
export const useGetProjectTreeWithKeyProject = ({ key }: { key: string }) => {
  return useQuery({
    queryKey: queryKeys.projects.tree(key),
    queryFn: () => getProjectTreeWithKey(key),
    enabled: key != null,
  });
};

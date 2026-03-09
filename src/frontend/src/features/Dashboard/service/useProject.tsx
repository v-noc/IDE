import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ProjectNodeTree } from "@/types/project";
import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";

interface GetProjectTreeParams {
  key: string;
  ref?: string;
}

const getProjectTreeWithKey = async ({
  key,
  ref,
}: GetProjectTreeParams): Promise<ProjectNodeTree> => {
  const search = new URLSearchParams({ project_id: key });
  if (ref) {
    search.set("ref", ref);
  }
  const response = await api(`${API_ROUTES.PROJECTS}?${search.toString()}`);
  return response as ProjectNodeTree;
};
export const useGetProjectTreeWithKeyProject = ({
  key,
  ref,
}: GetProjectTreeParams) => {
  return useQuery({
    queryKey: queryKeys.projects.tree(key, ref),
    queryFn: () => getProjectTreeWithKey({ key, ref }),
    enabled: key != null,
  });
};

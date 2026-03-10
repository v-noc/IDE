import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ProjectNodeTree } from "@/types/project";
import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

interface GetProjectTreeParams {
  key: string;
}

const getProjectTreeWithKey = async ({
  key,
}: GetProjectTreeParams): Promise<ProjectNodeTree> => {
  const search = new URLSearchParams({ project_id: key });
  const response = await api(`${API_ROUTES.PROJECTS}?${search.toString()}`);
  return response as ProjectNodeTree;
};
export const useGetProjectTreeWithKeyProject = ({
  key,
}: GetProjectTreeParams) => {
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);

  return useQuery({
    queryKey: queryKeys.projects.tree(key, branch, ref),
    queryFn: () => getProjectTreeWithKey({ key }),
    enabled: key != null,
  });
};

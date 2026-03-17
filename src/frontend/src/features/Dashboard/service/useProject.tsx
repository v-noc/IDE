import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ProjectNodeTree } from "@/types/project";
import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

interface GetProjectTreeParams {
  key: string;
  compareTo?: string | null;
}

const getProjectTreeWithKey = async ({
  key,
  compareTo,
}: GetProjectTreeParams): Promise<ProjectNodeTree> => {
  const search = new URLSearchParams({ project_id: key });
  const response = await api(`${API_ROUTES.PROJECTS}?${search.toString()}`, {
    compareTo: compareTo ?? undefined,
  });
  return response as ProjectNodeTree;
};
export const useGetProjectTreeWithKeyProject = ({
  key,
}: GetProjectTreeParams) => {
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  return useQuery({
    queryKey: queryKeys.projects.tree(key, branch, ref, compareTo),
    queryFn: () => getProjectTreeWithKey({ key, compareTo }),
    enabled: key != null,
  });
};

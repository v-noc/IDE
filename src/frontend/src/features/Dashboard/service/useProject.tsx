import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { ProjectNodeTree } from "@/types/project";
import { useQuery } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";

interface ProjectTreeQueryParams {
  key: string;
  compareTo?: string | null;
}

/** Full graph (folders, files, code) — e.g. after project create. */
const fetchProjectFullTree = async ({
  key,
  compareTo,
}: ProjectTreeQueryParams): Promise<ProjectNodeTree> => {
  const search = new URLSearchParams({ project_id: key });
  const response = await api(`${API_ROUTES.PROJECTS}?${search.toString()}`, {
    compareTo: compareTo ?? undefined,
  });
  return response as ProjectNodeTree;
};

/** Structure only (folders, files, groups) for sidebar + zustand. */
const fetchProjectStructureTree = async ({
  key,
  compareTo,
}: ProjectTreeQueryParams): Promise<ProjectNodeTree> => {
  const search = new URLSearchParams({ project_id: key });
  const response = await api(
    `${API_ROUTES.PROJECT_STRUCTURE}?${search.toString()}`,
    { compareTo: compareTo ?? undefined },
  );
  return response as ProjectNodeTree;
};

/**
 * Loads the full project tree into react-query (not used for sidebar store).
 */
export const useGetProjectFullTree = ({ key }: ProjectTreeQueryParams) => {
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  return useQuery({
    queryKey: queryKeys.projects.tree(key, branch, ref, compareTo),
    queryFn: () => fetchProjectFullTree({ key, compareTo }),
    enabled: key != null && key.length > 0,
  });
};

/**
 * Sidebar / dashboard: structure shell; code children load via `useLazyCodeChildren` + `/code-elements/descendants`.
 */
export const useGetProjectStructureTree = ({ key }: ProjectTreeQueryParams) => {
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  return useQuery({
    queryKey: queryKeys.projects.structureTree(
      key,
      branch,
      ref,
      compareTo,
      false,
    ),
    queryFn: () => fetchProjectStructureTree({ key, compareTo }),
    enabled: key != null && key.length > 0,
  });
};

/** @deprecated Use useGetProjectStructureTree for sidebar; useGetProjectFullTree when you need the full graph. */
export const useGetProjectTreeWithKeyProject = useGetProjectStructureTree;

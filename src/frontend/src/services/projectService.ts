
import { api } from '@/lib/api';
import API_ROUTES from '@/lib/apiRoutes';
import type { ProjectNode, ProjectNodeTree } from '@/types/project';
import { codeApi, type CodeDescendantsResponse } from '@/services/code/api';

export type { CodeDescendantsResponse };

// API functions using the new client
export const fetchProjects = (): Promise<ProjectNode[]> => {
  return api(`${API_ROUTES.PROJECTS}all`);
};

export const createProject = (newProject: { name: string; description: string; path: string }): Promise<ProjectNodeTree> => {
  return api(API_ROUTES.PROJECTS, { body: newProject, method: 'POST' });
};

export const fetchProjectStructureTree = (
  projectId: string,
  opts?: { excludeGroups?: boolean; compareTo?: string | null }
): Promise<ProjectNodeTree> => {
  const params = new URLSearchParams({ project_id: projectId });
  if (opts?.excludeGroups) params.set('exclude_groups', 'true');
  return api(`${API_ROUTES.PROJECT_STRUCTURE}?${params.toString()}`, {
    compareTo: opts?.compareTo ?? undefined,
  }) as Promise<ProjectNodeTree>;
};

export const fetchProjectCodeDescendants = (
  projectId: string,
  parentId: string,
  opts?: {
    depthStart?: number;
    depthMax?: number;
    childTypes?: string;
    compareTo?: string | null;
  }
): Promise<CodeDescendantsResponse> =>
  codeApi.getDescendants(projectId, parentId, opts);

export const deleteProject = (project_key: string) => {
  return api(API_ROUTES.PROJECTS + `?project_id=${project_key}`, { method: 'DELETE' })
}

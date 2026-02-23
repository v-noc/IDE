
import { api } from '@/lib/api';
import API_ROUTES from '@/lib/apiRoutes';
import type { ProjectNode, ProjectNodeTree } from '@/types/project';



// API functions using the new client
export const fetchProjects = (): Promise<ProjectNode[]> => {
  return api(`${API_ROUTES.PROJECTS}all`);
};

export const createProject = (newProject: { name: string; description: string; path: string }): Promise<ProjectNodeTree> => {
  return api(API_ROUTES.PROJECTS, { body: newProject, method: 'POST' });
};


export const deleteProject = (project_key: string) => {
  return api(API_ROUTES.PROJECTS + project_key, { method: 'DELETE' })
}

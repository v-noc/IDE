import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../lib/api';

interface Project {
  key: string;
  name: string;
  path: string;
}

// API functions using the new client
const fetchProjects = (): Promise<Project[]> => {
  return apiClient('/projects/');
};

const createProject = (newProject: { name: string; path: string }): Promise<Project> => {
  return apiClient('/projects/', { body: newProject });
};

// React Query hooks (no changes needed here)
export const useProjects = () => {
  return useQuery<Project[], Error>({
    queryKey: ['projects'],
    queryFn: fetchProjects,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation<Project, Error, { name: string; path: string }>({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
};

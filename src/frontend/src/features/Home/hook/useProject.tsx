import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { ProjectNodeTree, ProjectNode } from "@/types/project";
import {
  fetchProjects,
  createProject,
  deleteProject,
} from "@/services/projectService";

// React Query hooks (no changes needed here)
export const useProjects = () => {
  return useQuery<ProjectNode[], Error>({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation<
    ProjectNodeTree,
    Error,
    { name: string; description: string; path: string }
  >({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
};

import { useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { ThemeConfig } from "@/features/Dashboard/store/useThemeStore";
import type { ProjectTreeResponse } from "@/features/Dashboard/service/useProject";
import API_ROUTES from "@/lib/apiRoutes";

// Low-level API functions
const updateNodeTheme = async (
  elementKey: string,
  theme: ThemeConfig
): Promise<ProjectTreeResponse> => {
  console.log(elementKey, " theme ", theme);
  return api<ProjectTreeResponse>(
    `${API_ROUTES.CORE}${elementKey}/update-node-theme`,
    {
      method: "POST",
      body: theme as unknown as BodyInit,
    }
  );
};

const updateNodeIcon = async (
  elementKey: string,
  icon: string
): Promise<ProjectTreeResponse> => {
  console.log(elementKey, " icon ", icon);
  return api<ProjectTreeResponse>(
    `${API_ROUTES.CORE}${elementKey}/update-icon`,
    {
      method: "POST",
      body: { icon } as unknown as BodyInit,
    }
  );
};

const updateNodeBasicInfo = async (
  elementKey: string,
  basicInfo: {
    name: string;
    description?: string;
  }
): Promise<ProjectTreeResponse> => {
  console.log(elementKey, " ", basicInfo);
  return api<ProjectTreeResponse>(
    `${API_ROUTES.CORE}${elementKey}/update-basic-info`,
    {
      method: "POST",
      body: basicInfo as unknown as BodyInit,
    }
  );
};

// Hooks
export const useUpdateNodeTheme = (projectKey?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      elementKey,
      theme,
    }: {
      elementKey: string;
      theme: ThemeConfig;
    }) => updateNodeTheme(elementKey, theme),
    onSuccess: async () => {
      if (projectKey) {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: ["projectTree", projectKey],
          }),
          queryClient.invalidateQueries({
            queryKey: ["virtualFolders", projectKey],
          }),
        ]);
      }
    },
  });
};

export const useUpdateNodeIcon = (projectKey?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ elementKey, icon }: { elementKey: string; icon: string }) =>
      updateNodeIcon(elementKey, icon),

    onSettled: async () => {
      if (projectKey) {
        await queryClient.invalidateQueries({
          queryKey: ["projectTree", projectKey],
        });
        await queryClient.invalidateQueries({
          queryKey: ["virtualFolders", projectKey],
        });
      }
    },
  });
};

export const useUpdateNodeBasicInfo = (projectKey?: string) => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      elementKey,
      basicInfo,
    }: {
      elementKey: string;
      basicInfo: { name: string; description?: string };
    }) => updateNodeBasicInfo(elementKey, basicInfo),

    onSettled: async () => {
      if (projectKey) {
        await queryClient.invalidateQueries({
          queryKey: ["projectTree", projectKey],
        });
      }
    },
  });
};

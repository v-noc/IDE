import { api } from "@/lib/api"

import API_ROUTES from "@/lib/apiRoutes";
import { useMutation } from "@tanstack/react-query";
import type { ThemeConfig } from "@/types/project";

type BasicInfo = {
  name: string;
  description: string;
  icon: string;
}

const updateBasicInfo = async (containerId: string, projectId: string, basicInfo: BasicInfo) => {
  const response = await api(
    `${API_ROUTES.CONTAINER}update-basic-info?container_id=${encodeURIComponent(containerId)}&project_id=${encodeURIComponent(projectId)}`,
    {
      method: "PUT",
      body: basicInfo,
    }
  );
  return response;
}

const updateTheme = async (containerId: string, projectId: string, theme: ThemeConfig) => {
  const response = await api(
    `${API_ROUTES.CONTAINER}update-theme?container_id=${encodeURIComponent(containerId)}&project_id=${encodeURIComponent(projectId)}`,
    {
      method: "PUT",
      body: theme,
    }
  );
  return response;
}

export const useUpdateBasicInfo = (containerId: string, projectId: string) => {
  return useMutation({
    mutationFn: (basicInfo: BasicInfo) => updateBasicInfo(containerId, projectId, basicInfo),
  });
}

export const useUpdateTheme = (containerId: string, projectId: string) => {
  return useMutation({
    mutationFn: (theme: ThemeConfig) => updateTheme(containerId, projectId, theme),
  });
}

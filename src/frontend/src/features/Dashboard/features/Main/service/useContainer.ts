import { api } from "@/lib/api"

import API_ROUTES from "@/lib/apiRoutes";
import { useMutation } from "@tanstack/react-query";
import type { ThemeConfig } from "@/types/project";

type BasicInfo = {
    name: string;
    description: string;
    icon: string;
}

const updateBasicInfo = async (containerId: string, basicInfo: BasicInfo) => {
    const response = await api(`${API_ROUTES.CONTAINER}${containerId}/update-basic-info`, {
        method: "PUT",
        body: basicInfo,
    });
    return response;
}

const updateTheme = async (containerId: string, theme: ThemeConfig) => {
    const response = await api(`${API_ROUTES.CONTAINER}${containerId}/update-theme`, {
        method: "PUT",
        body: theme,
    });
    return response;
}

export const useUpdateBasicInfo = (containerId: string) => {
    return useMutation({
        mutationFn: (basicInfo: BasicInfo) => updateBasicInfo(containerId, basicInfo),
    });
}

export const useUpdateTheme = (containerId: string) => {
    return useMutation({
        mutationFn: (theme: ThemeConfig) => updateTheme(containerId, theme),
    });
}
import { api } from "@/lib/api"

import API_ROUTES from "@/lib/apiRoutes";
import { useMutation } from "@tanstack/react-query";

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

export const useUpdateBasicInfo = (containerId: string) => {
    return useMutation({
        mutationFn: (basicInfo: BasicInfo) => updateBasicInfo(containerId, basicInfo),
    });
}
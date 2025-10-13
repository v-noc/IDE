import {
    useQuery,
    useMutation,
    useQueryClient,
} from "@tanstack/react-query";

import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { NodeType } from "@/types/project";

export interface CodeResponse {
    file_id: string;
    file_name: string;
    file_path: string;
    node_type: NodeType;
    qname: string;
    code: string;
}

export interface WriteCodePayload {
    elementId: string;
    code: string;
}

const fetchCodeForNode = (elementId: string): Promise<CodeResponse> => {
    return api(`${API_ROUTES.CODE_ELEMENTS}${elementId}/code`);
};

const fetchFileCode = (fileId: string): Promise<CodeResponse> => {
    return api(`${API_ROUTES.CODE_ELEMENTS}${fileId}/file-code`);
};

const writeCode = (payload: WriteCodePayload) => {
    const { elementId, code } = payload;
    return api(`${API_ROUTES.CODE_ELEMENTS}${elementId}/write-code`, {
        method: "POST",
        body: { code },
    });
};

export const useGetCodeForNode = (elementId: string) => {
    return useQuery({
        queryKey: ["code", elementId],
        queryFn: () => fetchCodeForNode(elementId),
        enabled: !!elementId,
        retry: 1,
    });
};

export const useGetFileCode = (fileId: string) => {
    return useQuery({
        queryKey: ["file_code", fileId],
        queryFn: () => fetchFileCode(fileId),
        enabled: !!fileId,
        retry: 1,
    });
};

export const useWriteCode = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: writeCode,
        onSuccess: (_, variables) => {
            // Invalidate and refetch the code query to show the updated content
            queryClient.invalidateQueries({
                queryKey: ["code", variables.elementId],
            });
            queryClient.invalidateQueries({
                queryKey: ["file_code", variables.elementId],
            });
            // Notify other parts of the app (e.g., Sidebar) to resync the tree
            window.dispatchEvent(new CustomEvent("code-saved"));
        },
    });
};

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";

export interface LogNode {
    id: string;
    created_at: string;
    timestamp: string;
    event_type: string;
    message: string;
    duration_ms: number | null;
    chain_id: string | null;
    payload: { [key: string]: unknown } | null;
    result: unknown | null;
    error: { [key: string]: unknown } | null;
}

export interface LogTreeNode extends LogNode {
    children: LogTreeNode[];
}

export const useFunctionLogTree = (functionId: string) => {
    return useQuery<LogTreeNode[]>({
        queryKey: ["functionLogTree", functionId],
        queryFn: async () => {
            const response = await api(`${API_ROUTES.LOGS}${functionId}/tree`);
            return response as LogTreeNode[];
        },
        enabled: !!functionId,
    });
};

export const useCallLogTree = (callId: string) => {
    return useQuery<LogTreeNode[]>({
        queryKey: ["callLogTree", callId],
        queryFn: async () => {
            const response = await api(`${API_ROUTES.LOGS}${callId}/tree`);
            return response as LogTreeNode[];
        },
        enabled: !!callId,
    });
};
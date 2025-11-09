import { api } from "@/lib/api";
import API_ROUTES from "@/lib/apiRoutes";
import type { CallNode } from "@/types/project";
import { useMutation, useQueryClient } from "@tanstack/react-query";

type AddCallRequest = {
  callee_target_id: string;
  name: string;
  description: string;
};

export const useAddCall = (caller_node_id: string, project_key: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (add_call: AddCallRequest) => addCall(caller_node_id, add_call),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });
};

export const useRemoveCall = (project_key: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (call_key: string) => removeCall(call_key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projectTree", project_key] });
    },
  });
};

const removeCall = async (call_key: string): Promise<void> => {
  await api(`${API_ROUTES.CALLS}${call_key}/remove-call`, {
    method: "DELETE",
  });
};

const addCall = async (
  caller_node_id: string,
  add_call: AddCallRequest
): Promise<CallNode> => {
  const response = await api(`${API_ROUTES.CALLS}${caller_node_id}/add-call`, {
    method: "POST",
    body: add_call,
  });
  return response as CallNode;
};

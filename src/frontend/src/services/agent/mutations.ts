import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import type { SendMessagePayload } from "@/types/agent";
import { agentApi } from "./api";

export function useSendAgentMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: SendMessagePayload) => agentApi.sendMessage(payload),
    onSuccess: (_data, variables) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.agent.conversations.detail(variables.conversation_id),
      });
    },
  });
}

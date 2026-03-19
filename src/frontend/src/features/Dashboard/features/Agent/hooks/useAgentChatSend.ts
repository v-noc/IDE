import { useMutation, useQueryClient } from "@tanstack/react-query";
import queryKeys from "@/lib/queryKeys";
import { agentApi } from "@/services/agent/api";
import { useSocket } from "@/services/socket";
import { useAgentLiveStore } from "../live/store/useAgentLiveStore";
import { useAgentUiStore } from "../store/useAgentUiStore";

const LIST_LIMIT = 50;

/**
 * Sends a user message. If there is no active conversation id (new chat), creates
 * the conversation on the server first, hydrates wire state, joins the socket room,
 * then posts the message.
 */
export function useAgentChatSend() {
  const queryClient = useQueryClient();
  const { socket } = useSocket();

  return useMutation({
    mutationFn: async (text: string) => {
      let cid = useAgentUiStore.getState().backendConversationId;
      if (!cid) {
        const meta = await agentApi.createConversation({
          title: "New conversation",
          description: "",
        });
        cid = meta.id;
        useAgentUiStore.getState().setBackendConversationId(cid);
        const wire = await agentApi.hydrateConversation(cid);
        useAgentLiveStore.getState().setWire(wire);
        if (socket?.connected) {
          socket.emit("join_conversation", cid);
        }
        void queryClient.invalidateQueries({
          queryKey: queryKeys.agent.conversations.list(LIST_LIMIT),
        });
      }
      return agentApi.sendMessage({
        conversation_id: cid,
        parts: [{ type: "text", text }],
      });
    },
    onSuccess: () => {
      const cid = useAgentUiStore.getState().backendConversationId;
      if (cid) {
        void queryClient.invalidateQueries({
          queryKey: queryKeys.agent.conversations.detail(cid),
        });
      }
      void queryClient.invalidateQueries({
        queryKey: queryKeys.agent.conversations.list(LIST_LIMIT),
      });
    },
  });
}

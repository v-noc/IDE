import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import queryKeys from "@/lib/queryKeys";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { agentApi } from "@/services/agent/api";
import { useSocket } from "@/services/socket";
import { isAgentPreviewConversationId } from "../constants/agentPreviewConversation";
import { useAgentLiveStore } from "../live/store/useAgentLiveStore";
import { useAgentUiStore } from "../store/useAgentUiStore";

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
      const projectId = useProjectStore.getState().projectData?.id;
      if (!projectId) {
        throw new Error("No project loaded; cannot use agent chat.");
      }

      let cid = useAgentUiStore.getState().backendConversationId;
      if (isAgentPreviewConversationId(cid)) {
        toast.message("Exit the UI sample", {
          description: "Start a new chat or pick a real conversation to send messages.",
        });
        throw new Error("Cannot send while viewing the local UI sample.");
      }
      if (!cid) {
        const meta = await agentApi.createConversation(projectId, {
          title: "New conversation",
          description: "",
        });
        cid = meta.id;
        useAgentUiStore.getState().setBackendConversationId(cid);
        const wire = await agentApi.hydrateConversation(projectId, cid);
        useAgentLiveStore.getState().setWire(wire);
        if (socket?.connected) {
          socket.emit("join_conversation", cid);
        }
        void queryClient.invalidateQueries({
          queryKey: queryKeys.agent.conversations.all(),
        });
      }
      return agentApi.sendMessage(projectId, {
        conversation_id: cid,
        parts: [{ type: "text", text }],
      });
    },
    onSuccess: () => {
      // Sidebar summaries only. Conversation detail stays live via `conversation:patch`
      // and the live store; refetching detail here races with streaming and wipes placeholders.
      void queryClient.invalidateQueries({
        queryKey: queryKeys.agent.conversations.all(),
      });
    },
  });
}

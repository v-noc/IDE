import { useCallback } from "react";
import { toast } from "sonner";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { postDecision } from "../stream/source";
import { useAgentRunStore } from "../store/useAgentRunStore";

export function useDecision() {
  const projectId = useProjectStore((s) => s.projectData?.id);
  const conversationId = useAgentRunStore((s) => s.activeConversationId);

  const decide = useCallback(
    async (
      toolCallId: string,
      decision: "approve" | "cancel",
      overrides?: Record<string, unknown>,
    ) => {
      if (!projectId || !conversationId) {
        toast.error("No active conversation");
        return;
      }
      try {
        await postDecision(projectId, conversationId, {
          tool_call_id: toolCallId,
          decision,
          overrides,
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Decision failed";
        if (message.includes("409") || message.includes("Conflict")) {
          toast.error("This run expired — ask again");
          return;
        }
        toast.error(message);
        throw err;
      }
    },
    [conversationId, projectId],
  );

  return { decide };
}

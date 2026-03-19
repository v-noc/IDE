import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { agentConversationHydrationQueryOptions } from "@/services/agent";
import { useAgentLiveStore } from "../store/useAgentLiveStore";

/**
 * When leaving a live conversation, clear the store once.
 */
function useResetLiveWhenLeaving(conversationId: string | null) {
  const prev = useRef<string | null>(null);

  useEffect(() => {
    const was = prev.current;
    prev.current = conversationId;
    if (was !== null && conversationId === null) {
      useAgentLiveStore.getState().reset();
    }
  }, [conversationId]);
}

/**
 * Push TanStack Query snapshot into the live store only when a fetch finishes
 * (`dataUpdatedAt`), not on every `query.data` reference change.
 */
export function useAgentConversationSync(conversationId: string | null) {
  useResetLiveWhenLeaving(conversationId);

  const query = useQuery(agentConversationHydrationQueryOptions(conversationId));

  useEffect(() => {
    if (!conversationId) return;
    const data = query.data;
    if (!data || data.id !== conversationId) return;
    useAgentLiveStore.getState().setWire(data);
  }, [conversationId, query.dataUpdatedAt]);
}

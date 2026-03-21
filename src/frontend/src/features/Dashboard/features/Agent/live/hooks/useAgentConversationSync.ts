import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
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
export function useAgentConversationSync(
  conversationId: string | null,
  projectId: string,
) {
  useResetLiveWhenLeaving(conversationId);

  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const query = useQuery(
    agentConversationHydrationQueryOptions(
      projectId,
      conversationId,
      branch,
      ref,
      compareTo,
    ),
  );

  useEffect(() => {
    if (!conversationId) return;
    const data = query.data;
    if (!data || data.id !== conversationId) return;
    const { activeStreams } = useAgentLiveStore.getState();
    // Hydration from REST must not clobber in-flight streams (placeholder + patch indices).
    if (activeStreams.size > 0) return;
    useAgentLiveStore.getState().setWire(data);
  }, [conversationId, query.dataUpdatedAt]);
}

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useEffectEvent } from "@/lib/react/useEffectEvent";
import queryKeys from "@/lib/queryKeys";
import { useConversationRoom, useSocket } from "@/services/socket";
import type {
  ConversationPatchPayload,
  StreamChunkPayload,
  StreamEndPayload,
  StreamErrorPayload,
  StreamStartPayload,
} from "@/types/agent";
import { useAgentLiveStore } from "../store/useAgentLiveStore";

/**
 * Subscribes to agent stream + patch events for one conversation.
 * Uses `useEffectEvent` so handlers stay fresh without re-subscribing on every render.
 */
export function useAgentConversationSocket(conversationId: string | null) {
  const { socket, isConnected } = useSocket();
  const queryClient = useQueryClient();

  useConversationRoom(conversationId ?? undefined);

  const onPatch = useEffectEvent((payload: ConversationPatchPayload) => {
    if (!conversationId || payload.conversation_id !== conversationId) return;
    useAgentLiveStore.getState().applyServerPatches(payload.patches);
  });

  const onStreamStart = useEffectEvent((payload: StreamStartPayload) => {
    if (!conversationId || payload.conversation_id !== conversationId) return;
    useAgentLiveStore.getState().onStreamStart(payload);
  });

  const onStreamChunk = useEffectEvent((payload: StreamChunkPayload) => {
    if (!conversationId) return;
    useAgentLiveStore.getState().onStreamChunk(payload, conversationId);
  });

  const onStreamEnd = useEffectEvent((payload: StreamEndPayload) => {
    if (!conversationId) return;
    useAgentLiveStore.getState().onStreamEnd(payload, conversationId);
  });

  const onStreamError = useEffectEvent((payload: StreamErrorPayload) => {
    if (!conversationId) return;
    useAgentLiveStore.getState().onStreamError(payload, conversationId);
  });

  useEffect(() => {
    if (!socket || !isConnected) return;

    const patch = (p: ConversationPatchPayload) => onPatch(p);
    const start = (p: StreamStartPayload) => onStreamStart(p);
    const chunk = (p: StreamChunkPayload) => onStreamChunk(p);
    const end = (p: StreamEndPayload) => onStreamEnd(p);
    const err = (p: StreamErrorPayload) => onStreamError(p);

    socket.on("conversation:patch", patch);
    socket.on("stream:start", start);
    socket.on("stream:chunk", chunk);
    socket.on("stream:end", end);
    socket.on("stream:error", err);

    return () => {
      socket.off("conversation:patch", patch);
      socket.off("stream:start", start);
      socket.off("stream:chunk", chunk);
      socket.off("stream:end", end);
      socket.off("stream:error", err);
    };
    // Handlers are `useEffectEvent` — stable; only re-bind when socket / connectivity changes.
  }, [socket, isConnected]);

  const patchFailed = useAgentLiveStore((s) => s.patchApplyFailed);

  useEffect(() => {
    if (!patchFailed || !conversationId) return;
    void queryClient.invalidateQueries({
      queryKey: queryKeys.agent.conversations.detail(conversationId),
    });
    useAgentLiveStore.getState().clearPatchFailure();
  }, [patchFailed, conversationId, queryClient]);
}

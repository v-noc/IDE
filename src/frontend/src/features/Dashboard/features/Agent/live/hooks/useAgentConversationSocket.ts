import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useEffectEvent } from "@/lib/react/useEffectEvent";
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
export function useAgentConversationSocket(
  conversationId: string | null,
  projectId: string,
) {
  const { socket } = useSocket();
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
    if (!socket) return;

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
    // Handlers are `useEffectEvent` — stable; bind as soon as the client instance exists.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- onPatch/onStream* are EffectEvents
  }, [socket]);

  const patchFailed = useAgentLiveStore((s) => s.patchApplyFailed);

  useEffect(() => {
    if (!patchFailed || !conversationId || !projectId) return;
    void queryClient.invalidateQueries({
      predicate: (q) => {
        const k = q.queryKey;
        return (
          Array.isArray(k) &&
          k[0] === "agent" &&
          k[1] === "conversations" &&
          k[2] === "detail" &&
          k[3] === projectId &&
          k[4] === conversationId
        );
      },
    });
    useAgentLiveStore.getState().clearPatchFailure();
  }, [patchFailed, conversationId, projectId, queryClient]);

  const sawDisconnect = useRef(false);
  useEffect(() => {
    if (!socket || !conversationId || !projectId) return;

    const onDisconnect = () => {
      sawDisconnect.current = true;
    };

    const onConnect = () => {
      if (!sawDisconnect.current) return;
      sawDisconnect.current = false;
      void queryClient.invalidateQueries({
        predicate: (q) => {
          const k = q.queryKey;
          return (
            Array.isArray(k) &&
            k[0] === "agent" &&
            k[1] === "conversations" &&
            k[2] === "detail" &&
            k[3] === projectId &&
            k[4] === conversationId
          );
        },
      });
    };

    socket.on("disconnect", onDisconnect);
    socket.on("connect", onConnect);
    return () => {
      socket.off("disconnect", onDisconnect);
      socket.off("connect", onConnect);
    };
  }, [socket, conversationId, projectId, queryClient]);
}

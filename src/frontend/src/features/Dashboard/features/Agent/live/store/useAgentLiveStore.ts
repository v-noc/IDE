import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { applyConversationPatches } from "@/lib/jsonPatch/applyConversationPatches";
import type { Operation } from "fast-json-patch";
import type {
  StreamChunkPayload,
  StreamEndPayload,
  StreamErrorPayload,
  StreamStartPayload,
} from "@/types/agent";
import type { WireConversation, WireMessage, WireTextPart } from "@/types/agent";

const STREAM_PLACEHOLDER = (streamId: string) => `stream:${streamId}`;

function isTextPart(p: unknown): p is WireTextPart {
  return (
    typeof p === "object" &&
    p !== null &&
    (p as WireTextPart).type === "text" &&
    typeof (p as WireTextPart).text === "string"
  );
}

function appendDeltaToFirstTextPart(
  message: WireMessage,
  delta: string,
): WireMessage {
  const parts = [...message.parts];
  if (parts.length === 0) {
    return {
      ...message,
      parts: [{ type: "text", text: delta }],
    };
  }
  const head = parts[0];
  if (isTextPart(head)) {
    parts[0] = { type: "text", text: head.text + delta };
  } else {
    parts.unshift({ type: "text", text: delta });
  }
  return { ...message, parts };
}

export interface AgentLiveState {
  wire: WireConversation | null;
  /** Stream ids currently receiving chunks for the active conversation */
  activeStreams: Set<string>;
  patchApplyFailed: boolean;
  setWire: (wire: WireConversation | null) => void;
  reset: () => void;
  clearPatchFailure: () => void;
  applyServerPatches: (patches: Operation[]) => void;
  onStreamStart: (payload: StreamStartPayload) => void;
  onStreamChunk: (payload: StreamChunkPayload, conversationId: string) => void;
  onStreamEnd: (payload: StreamEndPayload, conversationId: string) => void;
  onStreamError: (payload: StreamErrorPayload, conversationId: string) => void;
}

export const useAgentLiveStore = create<AgentLiveState>()(
  devtools(
    (set, get) => ({
      wire: null,
      activeStreams: new Set(),
      patchApplyFailed: false,

      setWire: (wire) =>
        set((s) => {
          if (s.wire === wire) return s;
          return {
            wire,
            activeStreams: new Set(),
            patchApplyFailed: false,
          };
        }),

      reset: () =>
        set((s) => {
          if (
            s.wire === null &&
            s.activeStreams.size === 0 &&
            !s.patchApplyFailed
          ) {
            return s;
          }
          return {
            wire: null,
            activeStreams: new Set(),
            patchApplyFailed: false,
          };
        }),

      clearPatchFailure: () =>
        set((s) => (s.patchApplyFailed ? { patchApplyFailed: false } : s)),

      applyServerPatches: (patches) => {
        const { wire } = get();
        if (!wire || patches.length === 0) return;
        try {
          const next = applyConversationPatches(wire, patches);
          set({ wire: next, patchApplyFailed: false });
        } catch {
          set({ patchApplyFailed: true });
        }
      },

      onStreamStart: (payload) => {
        const { wire } = get();
        if (!wire || wire.id !== payload.conversation_id) return;
        const streamId = payload.stream_id;
        const placeholderId = STREAM_PLACEHOLDER(streamId);
        if (wire.messages.some((m) => m.id === placeholderId)) return;

        const seq = wire.messages.length;
        const placeholder: WireMessage = {
          id: placeholderId,
          role: "assistant",
          sequence: seq,
          parts: [{ type: "text", text: "" }],
          created_at: new Date().toISOString(),
          model: payload.model ?? null,
        };

        set({
          wire: {
            ...wire,
            messages: [...wire.messages, placeholder],
          },
          activeStreams: new Set(get().activeStreams).add(streamId),
        });
      },

      onStreamChunk: (payload, conversationId) => {
        const { wire } = get();
        if (!wire || wire.id !== conversationId) return;
        const placeholderId = STREAM_PLACEHOLDER(payload.stream_id);
        const idx = wire.messages.findIndex((m) => m.id === placeholderId);
        if (idx < 0) return;
        const nextMessages = [...wire.messages];
        nextMessages[idx] = appendDeltaToFirstTextPart(
          nextMessages[idx],
          payload.delta,
        );
        set({ wire: { ...wire, messages: nextMessages } });
      },

      onStreamEnd: (payload, conversationId) => {
        const { wire } = get();
        if (wire && wire.id !== conversationId) return;
        const next = new Set(get().activeStreams);
        next.delete(payload.stream_id);
        set({ activeStreams: next });
      },

      onStreamError: (payload, conversationId) => {
        const { wire } = get();
        if (!wire || wire.id !== conversationId) return;
        const placeholderId = STREAM_PLACEHOLDER(payload.stream_id);
        const messages = wire.messages.filter((m) => m.id !== placeholderId);
        const next = new Set(get().activeStreams);
        next.delete(payload.stream_id);
        set({
          wire: { ...wire, messages },
          activeStreams: next,
        });
      },
    }),
    { name: "agent-live-store" },
  ),
);

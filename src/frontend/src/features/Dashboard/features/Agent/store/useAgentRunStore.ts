import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { ConversationSummary, EffortLevel, NodeRefPart } from "../stream/types";

export type AgentViewMode = "chat" | "walkthrough";

export type StreamConnectionStatus =
  | "idle"
  | "streaming"
  | "error";

interface AgentRunState {
  activeConversationId: string | null;
  summaries: ConversationSummary[];
  viewMode: AgentViewMode;
  streamStatus: StreamConnectionStatus;
  streamError: string | null;
  effort: EffortLevel;
  pendingAttachments: NodeRefPart[];
  setActiveConversationId: (id: string | null) => void;
  setSummaries: (summaries: ConversationSummary[]) => void;
  setViewMode: (mode: AgentViewMode) => void;
  setStreamStatus: (
    status: StreamConnectionStatus,
    error?: string | null,
  ) => void;
  setEffort: (effort: EffortLevel) => void;
  addAttachment: (part: NodeRefPart) => void;
  removeAttachment: (nodeId: string) => void;
  clearAttachments: () => void;
}

const MAX_ATTACHMENTS = 3;

export const useAgentRunStore = create<AgentRunState>()(
  devtools(
    (set) => ({
      activeConversationId: null,
      summaries: [],
      viewMode: "chat",
      streamStatus: "idle",
      streamError: null,
      effort: "medium",
      pendingAttachments: [],
      setActiveConversationId: (id) =>
        set({ activeConversationId: id }, false, "setActiveConversationId"),
      setSummaries: (summaries) =>
        set({ summaries }, false, "setSummaries"),
      setViewMode: (mode) => set({ viewMode: mode }, false, "setViewMode"),
      setStreamStatus: (status, error = null) =>
        set(
          { streamStatus: status, streamError: error },
          false,
          "setStreamStatus",
        ),
      setEffort: (effort) => set({ effort }, false, "setEffort"),
      addAttachment: (part) =>
        set(
          (state) => {
            if (state.pendingAttachments.some((p) => p.node_id === part.node_id)) {
              return state;
            }
            if (state.pendingAttachments.length >= MAX_ATTACHMENTS) {
              return state;
            }
            return {
              pendingAttachments: [...state.pendingAttachments, part],
            };
          },
          false,
          "addAttachment",
        ),
      removeAttachment: (nodeId) =>
        set(
          (state) => ({
            pendingAttachments: state.pendingAttachments.filter(
              (p) => p.node_id !== nodeId,
            ),
          }),
          false,
          "removeAttachment",
        ),
      clearAttachments: () =>
        set({ pendingAttachments: [] }, false, "clearAttachments"),
    }),
    { name: "agent-run-store" },
  ),
);

export { MAX_ATTACHMENTS };

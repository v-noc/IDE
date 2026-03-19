import { create } from "zustand";
import { devtools } from "zustand/middleware";

/**
 * Which backend conversation is driving the live agent (patches + streams).
 * `null` means a local “new chat” draft; the server conversation is created on first send.
 */
export interface AgentUiState {
  backendConversationId: string | null;
  setBackendConversationId: (id: string | null) => void;
}

export const useAgentUiStore = create<AgentUiState>()(
  devtools(
    (set) => ({
      backendConversationId: null,
      setBackendConversationId: (id) => set({ backendConversationId: id }),
    }),
    { name: "agent-ui-store" },
  ),
);

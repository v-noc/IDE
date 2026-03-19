import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type { Conversation } from "../types/conversation";

/**
 * Local conversation object for replay / walkthrough demos (optional).
 * Live agent UI is driven by `useAgentUiStore.backendConversationId` + wire hydration.
 */
export interface ConversationState {
  currentConversation: Conversation | null;
  clearCurrentConversation: () => void;
}

export const useConversationStore = create<ConversationState>()(
  devtools(
    (set) => ({
      currentConversation: null,
      clearCurrentConversation: () => set({ currentConversation: null }),
    }),
    { name: "conversation-store" },
  ),
);

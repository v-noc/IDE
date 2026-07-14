import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  Conversation,
  ConversationSummary,
  ViewMode,
} from "../types/conversation";

/**
 * Legacy store for cognitive-replay fixtures (client-side only).
 * Live chat uses useMirrorStore + useAgentRunStore.
 */
export interface ConversationState {
  allConversations: Conversation[];
  currentConversation: Conversation | null;
  viewMode: ViewMode;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversationId: string) => void;
  clearCurrentConversation: () => void;
  setViewMode: (mode: ViewMode) => void;
}

export const useConversationStore = create<ConversationState>()(
  devtools(
    (set) => ({
      allConversations: [],
      currentConversation: null,
      viewMode: "chat",
      setConversations: (conversations) =>
        set(() => ({
          allConversations: conversations,
          currentConversation: conversations[0] ?? null,
        })),
      setCurrentConversation: (conversationId) =>
        set((state) => ({
          currentConversation:
            state.allConversations.find(
              (conversation) => conversation.id === conversationId,
            ) ?? state.currentConversation,
        })),
      clearCurrentConversation: () => set({ currentConversation: null }),
      setViewMode: (mode) => set({ viewMode: mode }),
    }),
    { name: "conversation-store" },
  ),
);

export const toConversationSummary = (
  conversation: Conversation,
): ConversationSummary => ({
  id: conversation.id,
  title: conversation.title,
  date: conversation.date,
  duration: conversation.duration,
});

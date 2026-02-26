import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { conversationFixtures } from "../fixtures/conversations";
import type {
  Conversation,
  ConversationSummary,
  ViewMode,
} from "../types/conversation";

export interface ConversationState {
  allConversations: Conversation[];
  currentConversation: Conversation | null;
  viewMode: ViewMode;
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversationId: string) => void;
  clearCurrentConversation: () => void;
  setViewMode: (mode: ViewMode) => void;
}

const initialConversations = conversationFixtures;

export const useConversationStore = create<ConversationState>()(
  devtools(
    (set) => ({
      allConversations: initialConversations,
      currentConversation: initialConversations[0] ?? null,
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

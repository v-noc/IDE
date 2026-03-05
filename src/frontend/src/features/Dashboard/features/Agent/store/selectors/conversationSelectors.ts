import type { ConversationSummary, MessagePart } from "../../types/conversation";
import type { ConversationState } from "../useConversationStore";
import { toConversationSummary } from "../useConversationStore";

export const selectConversationSummaries = (
  state: ConversationState,
): ConversationSummary[] => state.allConversations.map(toConversationSummary);

export const selectMessages = (state: ConversationState) =>
  state.currentConversation?.messages ?? [];

export const selectMessageText = (parts: MessagePart[]): string =>
  parts
    .filter((part): part is Extract<MessagePart, { type: "text" }> => {
      return part.type === "text";
    })
    .map((part) => part.text)
    .join("");

export const selectAllEvents = (state: ConversationState) =>
  selectMessages(state).flatMap((message) =>
    message.parts
      .filter((part): part is Extract<MessagePart, { type: "event" }> => {
        return part.type === "event";
      })
      .map((part) => part.event),
  );

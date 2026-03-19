import type { MessagePart } from "../../types/conversation";

export const selectMessageText = (parts: MessagePart[]): string =>
  parts
    .filter((part): part is Extract<MessagePart, { type: "text" }> => {
      return part.type === "text";
    })
    .map((part) => part.text)
    .join("");

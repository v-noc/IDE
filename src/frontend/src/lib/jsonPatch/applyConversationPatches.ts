import { applyPatch, type Operation } from "fast-json-patch";

export class ConversationPatchError extends Error {
  constructor(
    message: string,
    readonly cause?: unknown,
  ) {
    super(message);
    this.name = "ConversationPatchError";
  }
}

/**
 * Immutable RFC 6902 apply for conversation documents.
 * On failure, callers should refetch `GET /conversations/meta` + messages.
 */
export function applyConversationPatches<T extends object>(
  document: T,
  patches: Operation[],
): T {
  if (patches.length === 0) {
    return document;
  }
  try {
    const clone = structuredClone(document);
    const { newDocument } = applyPatch(clone, patches, false, true);
    return newDocument as T;
  } catch (e) {
    throw new ConversationPatchError("Failed to apply conversation patch", e);
  }
}

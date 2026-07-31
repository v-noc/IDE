import { useMirrorStore } from "../store/useMirrorStore";
import type { Conversation } from "../stream/types";

/** Re-seed closed artifact docs from a persisted conversation snapshot. */
export function seedConversationArtifacts(conversation: Conversation): void {
  const artifacts = conversation.artifacts;
  if (!artifacts) return;

  const { docs, seedDoc } = useMirrorStore.getState();
  for (const [doc, snapshot] of Object.entries(artifacts)) {
    if (!docs[doc]) {
      seedDoc(doc, snapshot);
    }
  }
}

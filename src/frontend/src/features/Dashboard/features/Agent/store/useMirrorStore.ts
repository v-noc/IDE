import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { applyFrame, type MirrorEntry } from "../stream/applyFrame";
import type { WireFrame } from "../stream/types";
import { isConversation, type Conversation } from "../stream/types";

interface MirrorState {
  docs: Record<string, MirrorEntry>;
  openDoc: (doc: string, snapshot: unknown) => void;
  applyFrames: (frames: WireFrame[]) => void;
  closeDoc: (doc: string, status: string, error?: string) => void;
  seedDoc: (doc: string, snapshot: unknown) => void;
  clearDoc: (doc: string) => void;
}

export const useMirrorStore = create<MirrorState>()(
  devtools(
    (set) => ({
      docs: {},

      openDoc: (doc, snapshot) =>
        set(
          (state) => ({
            docs: applyFrame(
              { kind: "open", doc, snapshot },
              state.docs,
            ),
          }),
          false,
          "openDoc",
        ),

      applyFrames: (frames) =>
        set(
          (state) => {
            let docs = state.docs;
            for (const frame of frames) {
              docs = applyFrame(frame, docs);
            }
            return { docs };
          },
          false,
          "applyFrames",
        ),

      closeDoc: (doc, status, error) =>
        set(
          (state) => ({
            docs: applyFrame(
              { kind: "close", doc, status, message: error },
              state.docs,
            ),
          }),
          false,
          "closeDoc",
        ),

      seedDoc: (doc, snapshot) =>
        set(
          (state) => ({
            docs: {
              ...state.docs,
              [doc]: {
                snapshot: structuredClone(snapshot),
                lastSeq: -1,
                status: "closed" as const,
              },
            },
          }),
          false,
          "seedDoc",
        ),

      clearDoc: (doc) =>
        set(
          (state) => {
            const { [doc]: _removed, ...rest } = state.docs;
            return { docs: rest };
          },
          false,
          "clearDoc",
        ),
    }),
    { name: "agent-mirror-store" },
  ),
);

export function selectConversation(
  docs: Record<string, MirrorEntry>,
  conversationId: string | null,
): Conversation | null {
  if (!conversationId) return null;
  const entry = docs[conversationId];
  if (!entry || !isConversation(entry.snapshot)) return null;
  return entry.snapshot;
}

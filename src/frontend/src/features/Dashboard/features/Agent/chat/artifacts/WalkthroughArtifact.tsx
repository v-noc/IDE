import { useEffect } from "react";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { useAgentRunStore } from "../../store/useAgentRunStore";
import { useMirrorStore } from "../../store/useMirrorStore";
import { getArtifact } from "../../stream/source";
import { TourOutline } from "../../walkthrough/components/TourOutline";
import { PlayControls } from "../../walkthrough/components/PlayControls";
import { flattenSession } from "../../walkthrough/store/flatten";
import { useWalkthroughStore } from "../../walkthrough/store/useWalkthroughStore";
import type { WalkthroughSession } from "../../walkthrough/types";

function isWalkthroughSession(value: unknown): value is WalkthroughSession {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return typeof v.id === "string" && Array.isArray(v.node_steps);
}

/** Mirror doc → existing walkthrough player store. */
export function useWalkthroughBridge(doc: string) {
  const entry = useMirrorStore((s) => s.docs[doc]);
  const conversationId = useAgentRunStore((s) => s.activeConversationId);
  const projectId = useProjectStore((s) => s.projectData?.id);
  const seedDoc = useMirrorStore((s) => s.seedDoc);

  useEffect(() => {
    if (entry || !conversationId || !projectId) return;

    let cancelled = false;
    void getArtifact(projectId, conversationId, doc)
      .then((snapshot) => {
        if (cancelled) return;
        seedDoc(doc, snapshot);
      })
      .catch((err) => {
        console.warn("[walkthrough] artifact reload failed", err);
      });

    return () => {
      cancelled = true;
    };
  }, [conversationId, doc, entry, projectId, seedDoc]);

  useEffect(() => {
    if (!entry || !isWalkthroughSession(entry.snapshot)) return;
    const session = entry.snapshot;
    const prev = useWalkthroughStore.getState();

    const phase =
      entry.status === "error"
        ? ("error" as const)
        : entry.status === "open"
          ? prev.phase === "playing"
            ? ("playing" as const)
            : ("generating" as const)
          : prev.phase === "playing"
            ? ("playing" as const)
            : ("ready" as const);

    useWalkthroughStore.setState({
      session,
      lastSeq: entry.lastSeq,
      phase,
      error: entry.error ?? null,
      playerSteps: flattenSession(session),
      cursor:
        prev.session?.id === session.id
          ? prev.cursor
          : -1,
    });
  }, [doc, entry]);
}

export function WalkthroughArtifact({ doc }: { doc: string }) {
  useWalkthroughBridge(doc);

  return (
    <div className="space-y-2 rounded-md border border-border/60 bg-background/60 p-2">
      <PlayControls />
      <TourOutline />
    </div>
  );
}

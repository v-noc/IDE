import { useCallback, useEffect } from "react";
import { toast } from "sonner";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import {
  cancelRun,
  createConversation,
  getConversation,
  listConversations,
  streamMessage,
} from "../stream/source";
import { seedConversationArtifacts } from "../stream/seedArtifacts";
import type { Part } from "../stream/types";
import { useAgentRunStore } from "../store/useAgentRunStore";
import { selectConversation, useMirrorStore } from "../store/useMirrorStore";

/** Shared across every useRunStream() caller in the tree. */
let sharedAbort: AbortController | null = null;

export function useConversations() {
  const projectId = useProjectStore((s) => s.projectData?.id);
  const setSummaries = useAgentRunStore((s) => s.setSummaries);
  const setActiveConversationId = useAgentRunStore(
    (s) => s.setActiveConversationId,
  );
  const seedDoc = useMirrorStore((s) => s.seedDoc);

  const refresh = useCallback(async () => {
    if (!projectId) return [];
    const summaries = await listConversations(projectId);
    setSummaries(summaries);
    return summaries;
  }, [projectId, setSummaries]);

  const load = useCallback(
    async (conversationId: string) => {
      if (!projectId) throw new Error("No project selected");
      const conversation = await getConversation(projectId, conversationId);
      seedDoc(conversation.id, conversation);
      seedConversationArtifacts(conversation);
      setActiveConversationId(conversation.id);
      return conversation;
    },
    [projectId, seedDoc, setActiveConversationId],
  );

  const create = useCallback(async () => {
    if (!projectId) throw new Error("No project selected");
    const conversation = await createConversation(projectId);
    seedDoc(conversation.id, conversation);
    setActiveConversationId(conversation.id);
    await refresh();
    return conversation;
  }, [projectId, refresh, seedDoc, setActiveConversationId]);

  useEffect(() => {
    if (!projectId) return;
    void refresh().catch((err) => {
      console.warn("[agent] list conversations failed", err);
    });
  }, [projectId, refresh]);

  return { refresh, load, create, projectId };
}

export function useRunStream() {
  const projectId = useProjectStore((s) => s.projectData?.id);
  const activeConversationId = useAgentRunStore((s) => s.activeConversationId);
  const setActiveConversationId = useAgentRunStore(
    (s) => s.setActiveConversationId,
  );
  const setStreamStatus = useAgentRunStore((s) => s.setStreamStatus);
  const streamStatus = useAgentRunStore((s) => s.streamStatus);
  const streamError = useAgentRunStore((s) => s.streamError);
  const seedDoc = useMirrorStore((s) => s.seedDoc);
  const { create, refresh } = useConversations();

  const conversation = useMirrorStore((s) =>
    selectConversation(s.docs, activeConversationId),
  );

  const stop = useCallback(async () => {
    sharedAbort?.abort();
    sharedAbort = null;
    if (projectId && activeConversationId) {
      try {
        await cancelRun(projectId, activeConversationId);
      } catch (err) {
        console.warn("[agent] cancel failed", err);
      }
    }
    setStreamStatus("idle");
  }, [activeConversationId, projectId, setStreamStatus]);

  const send = useCallback(
    async (
      parts: Part[],
      sendOptions?: { toolHint?: string },
    ) => {
      if (!projectId) {
        toast.error("Open a project before chatting");
        return;
      }

      let conversationId = activeConversationId;
      if (!conversationId) {
        const created = await create();
        conversationId = created.id;
      }

      sharedAbort?.abort();
      const controller = new AbortController();
      sharedAbort = controller;
      setStreamStatus("streaming");

      try {
        await streamMessage(
          projectId,
          conversationId,
          parts,
          (frames) => {
            useMirrorStore.getState().applyFrames(frames);
          },
          controller.signal,
          {
            effort: useAgentRunStore.getState().effort,
            toolHint: sendOptions?.toolHint,
          },
        );
        setStreamStatus("idle");
        void refresh();
      } catch (err) {
        if (controller.signal.aborted) {
          setStreamStatus("idle");
          return;
        }
        const message =
          err instanceof Error ? err.message : "Connection lost";
        setStreamStatus("error", message);
        toast.error(message);
      } finally {
        if (sharedAbort === controller) {
          sharedAbort = null;
        }
      }
    },
    [activeConversationId, create, projectId, refresh, setStreamStatus],
  );

  useEffect(() => {
    if (!activeConversationId || !projectId) return;
    const existing = selectConversation(
      useMirrorStore.getState().docs,
      activeConversationId,
    );
    if (existing) return;
    void getConversation(projectId, activeConversationId)
      .then((loaded) => {
        seedDoc(loaded.id, loaded);
        seedConversationArtifacts(loaded);
        setActiveConversationId(loaded.id);
      })
      .catch((err) => {
        console.warn("[agent] reload conversation failed", err);
      });
  }, [activeConversationId, projectId, seedDoc, setActiveConversationId]);

  return {
    send,
    stop,
    status: streamStatus,
    streamError,
    conversation,
    conversationId: activeConversationId,
    isStreaming: streamStatus === "streaming",
  };
}

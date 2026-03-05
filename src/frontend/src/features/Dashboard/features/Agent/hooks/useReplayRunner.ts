import { useEffect, useMemo, useRef } from "react";
import { ReplayRunner } from "../engine/ReplayRunner";
import { createDefaultRegistry } from "../engine/registry";
import { useConversationStore } from "../store/useConversationStore";
import { useReplayStore } from "../store/useReplayStore";
import type { MessagePart } from "../types/conversation";

export function useReplayRunner() {
  const runnerRef = useRef<ReplayRunner | null>(null);
  const currentConversation = useConversationStore(
    (state) => state.currentConversation,
  );
  const speed = useReplayStore((state) => state.speed);

  const events = useMemo(
    () =>
      (currentConversation?.messages ?? []).flatMap((message) =>
        message.parts
          .filter((part): part is Extract<MessagePart, { type: "event" }> => {
            return part.type === "event";
          })
          .map((part) => part.event),
      ),
    [currentConversation],
  );

  useEffect(() => {
    const runner = new ReplayRunner(createDefaultRegistry(), {
      onStatusChange: (status) => useReplayStore.getState().setStatus(status),
      onProgress: (index, event) => useReplayStore.getState().setProgress(index, event),
      onComplete: () => useReplayStore.getState().setStatus("idle"),
    });

    runnerRef.current = runner;
    return () => runner.stop();
  }, []);

  useEffect(() => {
    useReplayStore.getState().setTotalEvents(events.length);
    useReplayStore.getState().reset();
    runnerRef.current?.load(events);
  }, [events]);

  useEffect(() => {
    runnerRef.current?.setSpeed(speed);
  }, [speed]);

  return runnerRef;
}

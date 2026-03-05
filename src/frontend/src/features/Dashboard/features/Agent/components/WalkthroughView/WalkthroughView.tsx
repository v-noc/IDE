import { useMemo } from "react";
import type { Conversation } from "../../types/conversation";
import { useReplayRunner } from "../../hooks/useReplayRunner";
import { useReplayStore } from "../../store/useReplayStore";
import { useShallow } from "zustand/react/shallow";
import { selectMessageText } from "../../store/selectors/conversationSelectors";
import { PlaybackBar } from "./PlaybackBar";

interface WalkthroughViewProps {
  conversation: Conversation | null;
}

export function WalkthroughView({ conversation }: WalkthroughViewProps) {
  const runnerRef = useReplayRunner();
  const [status, currentEvent, totalEvents, currentIndex] = useReplayStore(
    useShallow((state) => [
      state.status,
      state.currentEvent,
      state.totalEvents,
      state.currentIndex,
    ]),
  );

  const ownerMessage = useMemo(() => {
    if (!conversation || !currentEvent) return null;

    return conversation.messages.find((message) =>
      message.parts.some(
        (part) => part.type === "event" && part.event.at === currentEvent.at,
      ),
    );
  }, [conversation, currentEvent]);

  if (!conversation) {
    return (
      <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
        No conversation selected.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-3 overflow-auto p-4">
        <section className="rounded-md border border-border bg-muted/40 p-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Current event
          </p>
          {currentEvent ? (
            <div className="mt-2 text-xs text-foreground">
              <p>
                <span className="font-medium">Type:</span> {currentEvent.type}
              </p>
              <p className="mt-1">
                <span className="font-medium">At:</span> {currentEvent.at}ms
              </p>
            </div>
          ) : (
            <p className="mt-2 text-xs text-muted-foreground">
              Press play to start walkthrough.
            </p>
          )}
        </section>

        {ownerMessage ? (
          <section className="rounded-md border border-border bg-muted/40 p-3">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              Message context
            </p>
            <p className="mt-2 text-xs leading-relaxed text-foreground">
              {selectMessageText(ownerMessage.parts) || "No message text."}
            </p>
          </section>
        ) : null}

        <section className="rounded-md border border-border bg-muted/40 p-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
            Status
          </p>
          <p className="mt-2 text-xs text-foreground">
            {status} ·{" "}
            {totalEvents === 0
              ? "0 / 0"
              : `${currentIndex + 1} / ${totalEvents}`}
          </p>
        </section>
      </div>

      <PlaybackBar runnerRef={runnerRef} />
    </div>
  );
}

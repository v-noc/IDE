import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { agentConversationHydrationQueryOptions } from "@/services/agent";
import { useConversationStore } from "../store/useConversationStore";
import { useAgentUiStore } from "../store/useAgentUiStore";
import { selectMessageText } from "../store/selectors/conversationSelectors";
import { useShallow } from "zustand/react/shallow";
import { useAgentChatSession } from "../live";
import { useAgentLiveStore } from "../live/store/useAgentLiveStore";
import { AgentChatInput } from "./AgentChatInput";
import { WalkthroughView } from "./WalkthroughView/WalkthroughView";
import {
  MessageList,
  messageItemFromWire,
  type MessageItemProps,
} from "./messages";

interface AgentSidebarProps {
  className?: string;
}

export function AgentSidebar({ className }: AgentSidebarProps) {
  const backendConversationId = useAgentUiStore((s) => s.backendConversationId);
  useAgentChatSession(backendConversationId);

  const wire = useAgentLiveStore((s) => s.wire);
  const activeStreams = useAgentLiveStore((s) => s.activeStreams);

  const hydrationQuery = useQuery(
    agentConversationHydrationQueryOptions(backendConversationId),
  );
  const isLiveLoading =
    Boolean(backendConversationId) && hydrationQuery.isPending;

  const [viewMode, setViewMode, currentConversation] = useConversationStore(
    useShallow((state) => [
      state.viewMode,
      state.setViewMode,
      state.currentConversation,
    ]),
  );

  const isLive =
    Boolean(backendConversationId) &&
    wire?.id === backendConversationId;

  const streamingPlaceholderIds = new Set(
    [...activeStreams].map((sid) => `stream:${sid}`),
  );

  let listMessages: MessageItemProps[] = [];
  if (isLive && wire) {
    listMessages = wire.messages.map((m) =>
      messageItemFromWire(m, {
        streaming: streamingPlaceholderIds.has(m.id),
      }),
    );
  } else if (currentConversation?.messages?.length) {
    listMessages = currentConversation.messages.map((m) => ({
      id: m.id,
      role: m.role,
      text: selectMessageText(m.parts),
    }));
  }

  const title = isLive
    ? (wire?.title ?? "Loading…")
    : (currentConversation?.title ?? "No conversation selected");

  return (
    <aside
      className={cn(
        "pointer-events-auto flex h-full w-full flex-col rounded-xl border border-border bg-background text-foreground shadow-lg",
        className,
      )}
    >
      <div className="border-b border-border px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            AI Cognitive Replay
            {isLive ? (
              <span className="ml-2 font-normal normal-case text-primary">
                · Live
              </span>
            ) : null}
          </p>
          <p className="mt-1 truncate text-xs text-foreground">{title}</p>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-auto p-4">
        {viewMode === "chat" ? (
          <section className="space-y-2">
            {isLiveLoading ? (
              <p className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
                Loading conversation…
              </p>
            ) : (
              <MessageList messages={listMessages} />
            )}
          </section>
        ) : isLive ? (
          <p className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
            Walkthrough mode is available for local demo conversations only.
            Select a fixture chat or switch to Chat.
          </p>
        ) : (
          <WalkthroughView conversation={currentConversation} />
        )}
      </div>

      <div className="border-t border-border p-3">
        <AgentChatInput />
        <div className="mt-3 flex justify-center">
          <div className="rounded-md border border-border p-0.5">
            <button
              type="button"
              onClick={() => setViewMode("chat")}
              className={cn(
                "rounded px-2 py-1 text-[11px] transition",
                viewMode === "chat"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              Chat
            </button>
            <button
              type="button"
              onClick={() => setViewMode("walkthrough")}
              className={cn(
                "rounded px-2 py-1 text-[11px] transition",
                viewMode === "walkthrough"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              Walkthrough
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}

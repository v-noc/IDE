import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { agentConversationHydrationQueryOptions } from "@/services/agent";
import { useAgentUiStore } from "../store/useAgentUiStore";
import { useAgentLiveStore } from "../live/store/useAgentLiveStore";
import { AgentChatInput } from "./AgentChatInput";
import { ChatContainer } from "./chat";

interface AgentSidebarProps {
  className?: string;
}

export function AgentSidebar({ className }: AgentSidebarProps) {
  const backendConversationId = useAgentUiStore((s) => s.backendConversationId);
  const projectId = useProjectStore((s) => s.projectData?.id ?? "");
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const wire = useAgentLiveStore((s) => s.wire);
  const activeStreams = useAgentLiveStore((s) => s.activeStreams);

  const hydrationQuery = useQuery(
    agentConversationHydrationQueryOptions(
      projectId,
      backendConversationId,
      branch,
      ref,
      compareTo,
    ),
  );
  const isLiveLoading =
    Boolean(backendConversationId) && hydrationQuery.isPending;

  const isLive =
    Boolean(backendConversationId) && wire?.id === backendConversationId;

  const streamingPlaceholderIds = new Set(
    [...activeStreams].map((sid) => `stream:${sid}`),
  );

  const listMessages = isLive && wire ? wire.messages : [];

  const title = !backendConversationId
    ? "New chat"
    : isLiveLoading
      ? "Loading…"
      : (wire?.title ?? "Conversation");

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
            Agent
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
        <section className="space-y-2">
          {isLiveLoading ? (
            <p className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
              Loading conversation…
            </p>
          ) : (
            <ChatContainer
              messages={listMessages}
              streamingMessageIds={streamingPlaceholderIds}
              emptyLabel={
                backendConversationId
                  ? "No messages yet."
                  : "New chat — your conversation is created when you send the first message."
              }
            />
          )}
        </section>
      </div>

      <div className="border-t border-border p-3">
        <AgentChatInput />
      </div>
    </aside>
  );
}

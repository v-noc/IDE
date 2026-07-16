import { cva } from "class-variance-authority";
import { useShallow } from "zustand/react/shallow";
import type { ConversationStatus } from "../stream/types";
import { useAgentRunStore } from "../store/useAgentRunStore";
import type { StreamConnectionStatus } from "../store/useAgentRunStore";

const statusDotVariants = cva("size-[7px] shrink-0 rounded-full", {
  variants: {
    status: {
      idle: "bg-agent-text-faint",
      streaming: "bg-agent-accent agent-status-dot--pulse",
      error: "bg-agent-danger",
      warn: "bg-agent-warn agent-status-dot--pulse",
    },
  },
  defaultVariants: {
    status: "idle",
  },
});

function resolveDotStatus(
  streamStatus: StreamConnectionStatus,
  conversationStatus?: ConversationStatus,
): "idle" | "streaming" | "error" | "warn" {
  if (conversationStatus === "awaiting_confirmation") return "warn";
  if (streamStatus === "streaming") return "streaming";
  if (streamStatus === "error" || conversationStatus === "error") return "error";
  return "idle";
}

function formatSessionId(conversationId: string | null): string | null {
  if (!conversationId) return null;
  return `session ${conversationId.slice(0, 8)}`;
}

interface PanelHeaderProps {
  conversationStatus?: ConversationStatus;
}

export function PanelHeader({ conversationStatus }: PanelHeaderProps) {
  const [activeConversationId, streamStatus] = useAgentRunStore(
    useShallow((state) => [state.activeConversationId, state.streamStatus]),
  );

  const sessionLabel = formatSessionId(activeConversationId);
  const dotStatus = resolveDotStatus(streamStatus, conversationStatus);

  return (
    <header className="flex h-12 shrink-0 items-center gap-2 border-b border-agent-header-border px-[18px]">
      <span
        className={statusDotVariants({ status: dotStatus })}
        aria-hidden="true"
      />
      <span className="text-[13px] font-semibold tracking-[0.04em] text-agent-text">
        AGENT
      </span>
      {sessionLabel ? (
        <span className="ml-auto font-agent-mono text-[10.5px] text-agent-text-faint">
          {sessionLabel}
        </span>
      ) : null}
    </header>
  );
}

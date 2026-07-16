import { useState } from "react";
import { Clock3, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useAgentOverlayStore } from "../store/useAgentOverlayStore";
import { useAgentRunStore } from "../store/useAgentRunStore";
import { useConversations } from "../hooks/useRunStream";
import { useShallow } from "zustand/react/shallow";
import { AgentPanel } from "./AgentPanel";

const PANEL_WIDTH = 420;

function formatUpdatedAt(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export function AgentOverlay() {
  const { isOpen, setOpen } = useAgentOverlayStore();
  const [summaries, activeConversationId, setActiveConversationId] =
    useAgentRunStore(
      useShallow((state) => [
        state.summaries,
        state.activeConversationId,
        state.setActiveConversationId,
      ]),
    );
  const { load, create } = useConversations();
  const [searchTerm, setSearchTerm] = useState("");

  const filteredHistory = summaries.filter((item) => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return true;
    return (
      item.title.toLowerCase().includes(query) ||
      item.id.toLowerCase().includes(query)
    );
  });

  return (
    <div className="pointer-events-none absolute inset-0 z-30">
      <div
        className="pointer-events-auto absolute top-0 right-0 bottom-24 h-full transition-transform duration-200"
        style={{
          width: PANEL_WIDTH,
          transform: isOpen ? "translateX(0)" : "translateX(100%)",
        }}
      >
        <div className="agent-v2 absolute top-2 right-2 z-10 flex items-center gap-0.5">
          <button
            type="button"
            aria-label="New conversation"
            onClick={() => void create()}
            className="flex size-7 items-center justify-center rounded-md text-agent-text-muted transition-colors hover:bg-agent-bg-raised hover:text-agent-text"
          >
            <Plus className="size-3.5" />
          </button>
          <Popover>
            <PopoverTrigger asChild>
              <button
                type="button"
                aria-label="Open chat history"
                className="flex size-7 items-center justify-center rounded-md text-agent-text-muted transition-colors hover:bg-agent-bg-raised hover:text-agent-text"
              >
                <Clock3 className="size-3.5" />
              </button>
            </PopoverTrigger>
            <PopoverContent
              align="end"
              side="bottom"
              className="agent-v2 w-80 border-agent-border-strong bg-agent-bg-card p-2 text-agent-text"
            >
              <div className="space-y-2">
                <p className="px-2 pt-1 text-[10px] font-bold tracking-[0.08em] text-agent-text-label">
                  CHAT HISTORY
                </p>
                <input
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  placeholder="Search chats…"
                  className="h-8 w-full rounded-agent-field border border-agent-border-strong bg-agent-bg-inset px-2 text-xs text-agent-text placeholder:text-agent-text-faint focus:outline-none focus:ring-1 focus:ring-agent-accent"
                />
                <div className="max-h-72 space-y-1 overflow-auto px-1 pb-1">
                  {filteredHistory.length > 0 ? (
                    filteredHistory.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => {
                          setActiveConversationId(item.id);
                          void load(item.id);
                        }}
                        className={cn(
                          "w-full rounded-agent-field px-2 py-2 text-left transition hover:bg-agent-bg-raised",
                          activeConversationId === item.id &&
                            "bg-agent-bg-raised",
                        )}
                      >
                        <p className="truncate text-xs font-medium text-agent-text">
                          {item.title.trim() || "Untitled"}
                        </p>
                        <p className="mt-1 font-agent-mono text-[11px] text-agent-text-muted">
                          {formatUpdatedAt(item.updated_at)} · {item.status}
                        </p>
                      </button>
                    ))
                  ) : (
                    <p className="px-2 py-4 text-center text-xs text-agent-text-muted">
                      No chat history yet.
                    </p>
                  )}
                </div>
              </div>
            </PopoverContent>
          </Popover>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close agent panel"
            className="flex size-7 items-center justify-center rounded-md text-agent-text-muted transition-colors hover:bg-agent-bg-raised hover:text-agent-text"
          >
            <X className="size-3.5" />
          </button>
        </div>
        <AgentPanel />
      </div>
    </div>
  );
}

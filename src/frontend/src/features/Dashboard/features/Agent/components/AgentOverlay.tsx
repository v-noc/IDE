import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";
import { Clock3, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { AgentSidebar } from "./AgentSidebar";
import { useAgentOverlayStore } from "../store/useAgentOverlayStore";
import { useAgentUiStore } from "../store/useAgentUiStore";
import { useShallow } from "zustand/react/shallow";
import { useVersioningStore } from "@/features/Dashboard/features/Versioning/store/useVersioningStore";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { agentConversationSummariesQueryOptions } from "@/services/agent";

const MIN_WIDTH = 280;
const DEFAULT_WIDTH = 360;
const MAX_WIDTH = 720;
const LIST_LIMIT = 50;

function formatUpdatedAt(iso: string) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return "";
  }
}

export function AgentOverlay() {
  const { isOpen, setOpen } = useAgentOverlayStore();
  const [backendConversationId, setBackendConversationId] = useAgentUiStore(
    useShallow((s) => [s.backendConversationId, s.setBackendConversationId]),
  );

  const projectId = useProjectStore((s) => s.projectData?.id ?? "");
  const branch = useVersioningStore((s) => s.branch);
  const ref = useVersioningStore((s) => s.checkedOutCommitId);
  const compareTo = useVersioningStore((s) => s.compareToCommitId);

  const serverQuery = useQuery(
    agentConversationSummariesQueryOptions(
      projectId,
      branch,
      ref,
      compareTo,
      LIST_LIMIT,
    ),
  );

  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const startResize = useCallback(() => {
    setIsResizing(true);
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (event: MouseEvent) => {
      const viewportMax = Math.min(MAX_WIDTH, window.innerWidth * 0.6);
      const nextWidth = window.innerWidth - event.clientX;
      const clampedWidth = Math.max(
        MIN_WIDTH,
        Math.min(viewportMax, nextWidth),
      );
      setWidth(clampedWidth);
    };

    const stopResize = () => {
      setIsResizing(false);
    };

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", stopResize);

    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", stopResize);
    };
  }, [isResizing]);

  const serverItems = serverQuery.data?.items ?? [];
  const filteredServer = serverItems.filter((item) => {
    const query = searchTerm.trim().toLowerCase();
    if (!query) return true;
    return (
      item.title.toLowerCase().includes(query) ||
      item.description.toLowerCase().includes(query)
    );
  });

  const startNewChat = () => {
    setBackendConversationId(null);
  };

  return (
    <div className="pointer-events-none absolute inset-0 z-30">
      <div
        className="pointer-events-auto absolute bottom-24 right-0 top-0 h-full transition-transform duration-200"
        style={{
          width,
          transform: isOpen ? "translateX(0)" : "translateX(100%)",
        }}
      >
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize agent overlay"
          onMouseDown={startResize}
          className="absolute left-0 top-0 h-full w-2 -translate-x-1 cursor-col-resize"
        />
        <div className="absolute right-2 top-2 z-10 flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={startNewChat}
            aria-label="Start new chat"
            title="New chat"
            className="h-7 w-7 text-muted-foreground hover:text-foreground"
          >
            <Plus size={14} />
          </Button>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Open chat history"
                className="h-7 w-7 text-muted-foreground hover:text-foreground"
              >
                <Clock3 size={14} />
              </Button>
            </PopoverTrigger>
            <PopoverContent align="end" side="bottom" className="w-80 p-2">
              <div className="space-y-3">
                <div className="flex items-center justify-between px-2 pt-1">
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    Chat history
                  </p>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="h-7 gap-1 px-2 text-[11px]"
                    onClick={startNewChat}
                  >
                    <Plus size={12} />
                    New chat
                  </Button>
                </div>
                <div className="px-2">
                  <Input
                    value={searchTerm}
                    onChange={(event) => setSearchTerm(event.target.value)}
                    placeholder="Search…"
                    className="h-8 text-xs"
                  />
                </div>

                <div className="max-h-72 space-y-1 overflow-auto px-1 pb-1">
                  {serverQuery.isError ? (
                    <p className="px-2 py-2 text-xs text-destructive">
                      Could not load conversations. Is the API running?
                    </p>
                  ) : serverQuery.isPending ? (
                    <p className="px-2 py-2 text-xs text-muted-foreground">
                      Loading…
                    </p>
                  ) : filteredServer.length > 0 ? (
                    filteredServer.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setBackendConversationId(item.id)}
                        className={cn(
                          "w-full rounded-sm px-2 py-2 text-left transition hover:bg-muted",
                          backendConversationId === item.id && "bg-muted",
                        )}
                      >
                        <p className="truncate text-xs font-medium text-foreground">
                          {item.title}
                        </p>
                        <p className="mt-1 text-[11px] text-muted-foreground">
                          {formatUpdatedAt(item.updated_at)} ·{" "}
                          {item.message_count} msgs
                        </p>
                      </button>
                    ))
                  ) : (
                    <p className="px-2 py-2 text-xs text-muted-foreground">
                      No conversations yet. Start a new chat and send a message.
                    </p>
                  )}
                </div>
              </div>
            </PopoverContent>
          </Popover>

          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setOpen(false)}
            aria-label="Close agent overlay"
            className="h-7 w-7 text-muted-foreground hover:text-foreground"
          >
            <X size={14} />
          </Button>
        </div>
        <AgentSidebar className="rounded-none" />
      </div>
    </div>
  );
}

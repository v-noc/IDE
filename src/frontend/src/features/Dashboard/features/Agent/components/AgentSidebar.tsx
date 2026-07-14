import { cn } from "@/lib/utils";
import { useShallow } from "zustand/react/shallow";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import useTabStore from "@/features/Dashboard/store/useTabStore";
import { findNodeByKey } from "@/features/Dashboard/utils/findNode";
import { Composer } from "../chat/Composer";
import { ChatThread } from "../chat/ChatThread";
import { WalkthroughPanel } from "../walkthrough";
import { useAgentRunStore } from "../store/useAgentRunStore";
import { useRunStream } from "../hooks/useRunStream";
import type { NodeRefPart } from "../stream/types";

interface AgentSidebarProps {
  className?: string;
}

export function AgentSidebar({ className }: AgentSidebarProps) {
  const [viewMode, setViewMode] = useAgentRunStore(
    useShallow((state) => [state.viewMode, state.setViewMode]),
  );
  const { conversation, streamError } = useRunStream();
  const activeTabId = useTabStore((s) => s.activeTabId);
  const projectData = useProjectStore((s) => s.projectData);
  const setSelectedNode = useProjectStore((s) => s.setSelectedNode);

  const focusNode = (part: NodeRefPart) => {
    if (!projectData) return;
    const node = findNodeByKey(projectData, part.node_id);
    if (node) setSelectedNode(activeTabId, node);
  };

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
          </p>
          <p className="mt-1 truncate text-xs text-foreground">
            {conversation?.title?.trim() || "New conversation"}
          </p>
        </div>
      </div>

      {viewMode === "chat" ? (
        <ChatThread
          conversation={conversation}
          connectionError={streamError}
          onFocusNode={focusNode}
        />
      ) : (
        <div className="flex-1 space-y-4 overflow-auto p-4">
          <WalkthroughPanel />
        </div>
      )}

      <div className="border-t border-border p-3">
        <Composer onFocusNode={focusNode} />
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

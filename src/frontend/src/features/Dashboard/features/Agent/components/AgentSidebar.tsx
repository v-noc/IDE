import { cn } from "@/lib/utils";
import { useConversationStore } from "../store/useConversationStore";
import { selectMessageText } from "../store/selectors/conversationSelectors";
import { useShallow } from "zustand/react/shallow";
import { AgentChatInput } from "./AgentChatInput";
import { WalkthroughPanel } from "../walkthrough";

interface AgentSidebarProps {
  className?: string;
}

export function AgentSidebar({ className }: AgentSidebarProps) {
  const [viewMode, setViewMode, currentConversation] = useConversationStore(
    useShallow((state) => [
      state.viewMode,
      state.setViewMode,
      state.currentConversation,
    ]),
  );

  const messages = currentConversation?.messages;

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
            Walkthrough Agent
          </p>
          <p className="mt-1 truncate text-xs text-foreground">
            {currentConversation?.title ?? "No conversation selected"}
          </p>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-auto p-4">
        {viewMode === "chat" ? (
          <section className="space-y-2">
            {messages && messages.length > 0 ? (
              messages.map((message) => (
                <article
                  key={message.id}
                  className="rounded-md border border-border bg-muted/40 p-3"
                >
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {message.role}
                  </p>
                  <p className="text-xs leading-relaxed text-foreground">
                    {selectMessageText(message.parts) || "No text content."}
                  </p>
                </article>
              ))
            ) : (
              <p className="rounded-md border border-border bg-muted/40 p-3 text-xs text-muted-foreground">
                No messages in this conversation.
              </p>
            )}
          </section>
        ) : (
          <WalkthroughPanel />
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

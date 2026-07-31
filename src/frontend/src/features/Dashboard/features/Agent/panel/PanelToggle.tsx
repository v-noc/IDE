import "../theme/tokens.css";

import { Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAgentOverlayStore } from "../store/useAgentOverlayStore";

export function PanelToggle() {
  const { isOpen, toggleOpen } = useAgentOverlayStore();

  return (
    <button
      type="button"
      onClick={toggleOpen}
      aria-label={isOpen ? "Hide agent panel" : "Show agent panel"}
      aria-pressed={isOpen}
      className={cn(
        "agent-v2 flex h-6 cursor-pointer items-center gap-1 rounded-xs px-2 py-1 text-xs font-medium transition-colors",
        isOpen
          ? "bg-agent-accent-bg text-agent-accent-text hover:bg-agent-accent-bg-subtle"
          : "text-agent-text-muted hover:bg-agent-bg-raised hover:text-agent-text",
      )}
    >
      <Bot size={12} />
      <span>Agent</span>
    </button>
  );
}

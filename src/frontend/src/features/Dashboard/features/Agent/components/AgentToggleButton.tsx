import { Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAgentOverlayStore } from "../store/useAgentOverlayStore";

export function AgentToggleButton() {
  const { isOpen, toggleOpen } = useAgentOverlayStore();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleOpen}
      className={`flex h-6 cursor-pointer items-center gap-1 rounded-xs px-2 py-1 text-xs font-medium transition-colors ${
        isOpen
          ? "bg-primary/10 text-primary hover:bg-primary/20"
          : "text-muted-foreground hover:bg-muted-foreground/10 hover:text-foreground"
      }`}
      aria-label={isOpen ? "Hide agent overlay" : "Show agent overlay"}
    >
      <Bot size={12} />
      <span>Agent</span>
    </Button>
  );
}

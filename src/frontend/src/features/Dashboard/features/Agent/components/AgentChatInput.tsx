import { useState } from "react";
import { SendHorizontal } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useAgentChatSend } from "../hooks/useAgentChatSend";

interface AgentChatInputProps {
  className?: string;
}

export function AgentChatInput({ className }: AgentChatInputProps) {
  const [value, setValue] = useState("");
  const sendMessage = useAgentChatSend();

  const handleSubmit = () => {
    const text = value.trim();
    if (!text) return;

    sendMessage.mutate(text, {
      onSuccess: () => setValue(""),
      onError: (e) => {
        toast.error("Failed to send message", {
          description: e instanceof Error ? e.message : String(e),
        });
      },
    });
  };

  return (
    <div className={cn("flex items-center ", className)}>
      <Input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
          }
        }}
        placeholder="Message…"
        className="h-9 text-xs"
      />
      <Button
        type="button"
        size="sm"
        onClick={handleSubmit}
        disabled={!value.trim() || sendMessage.isPending}
        className="h-9 px-3"
        aria-label="Send message"
      >
        <SendHorizontal size={14} />
      </Button>
    </div>
  );
}

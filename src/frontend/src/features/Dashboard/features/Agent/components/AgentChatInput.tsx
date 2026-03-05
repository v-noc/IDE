import { useState } from "react";
import { SendHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface AgentChatInputProps {
  className?: string;
}

export function AgentChatInput({ className }: AgentChatInputProps) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    // Input UI only for now; sending logic is intentionally out of scope.
    setValue("");
  };

  return (
    <div className={cn("flex items-center ", className)}>
      <Input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Ask AI about this code..."
        className="h-9 text-xs"
      />
      <Button
        type="button"
        size="sm"
        onClick={handleSubmit}
        disabled={!value.trim()}
        className="h-9 px-3"
        aria-label="Send message"
      >
        <SendHorizontal size={14} />
      </Button>
    </div>
  );
}

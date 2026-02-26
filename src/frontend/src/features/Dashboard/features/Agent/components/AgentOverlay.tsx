import { useCallback, useEffect, useState } from "react";
import { Clock3, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { AgentSidebar } from "./AgentSidebar";
import { useAgentOverlayStore } from "../store/useAgentOverlayStore";

const MIN_WIDTH = 280;
const DEFAULT_WIDTH = 360;
const MAX_WIDTH = 720;
const CHAT_HISTORY_ITEMS = [
  "Analyze dependency graph",
  "Explain selected node changes",
  "Summarize version diff",
  "Generate test checklist",
];

export function AgentOverlay() {
  const { isOpen, setOpen } = useAgentOverlayStore();
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);

  const startResize = useCallback(() => {
    setIsResizing(true);
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (event: MouseEvent) => {
      const viewportMax = Math.min(MAX_WIDTH, window.innerWidth * 0.6);
      const nextWidth = window.innerWidth - event.clientX;
      const clampedWidth = Math.max(MIN_WIDTH, Math.min(viewportMax, nextWidth));
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

  return (
    <div className="pointer-events-none absolute inset-0 z-30">
      <div
        className="absolute bottom-24 right-0 top-0 h-full pointer-events-auto transition-transform duration-200"
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
            <PopoverContent align="end" side="bottom" className="w-64 p-2">
              <div className="space-y-1">
                <p className="px-2 pb-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                  Chat history
                </p>
                {CHAT_HISTORY_ITEMS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className="w-full rounded-sm px-2 py-1.5 text-left text-xs text-foreground transition hover:bg-muted"
                  >
                    {item}
                  </button>
                ))}
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

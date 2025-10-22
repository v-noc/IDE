import React, { useState } from "react";

import { ChevronLeft } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { RightSidebar } from "./components/RightSidebar";

const MainWithRightSidebar: React.FC<{
  left: React.ReactNode;

  defaultOpen?: boolean;
  rightDefaultSize?: number; // percentage
  rightMinSize?: number; // percentage
  className?: string;
}> = ({
  left,

  defaultOpen = true,
  className,
  rightDefaultSize = 25,
  rightMinSize = 15,
}) => {
  const [open, setOpen] = useState<boolean>(Boolean(defaultOpen));
  return (
    <div
      className={`relative h-full w-full min-h-0 overflow-hidden ${
        className ?? ""
      }`}
    >
      <ResizablePanelGroup direction="horizontal" className="h-full min-h-0">
        <ResizablePanel
          defaultSize={open ? 100 - rightDefaultSize : 100}
          minSize={40}
          className="h-full min-h-0"
        >
          {left}
        </ResizablePanel>

        {open ? (
          <>
            <ResizableHandle className="hover:bg-border/70 transition-colors" />
            <ResizablePanel
              defaultSize={rightDefaultSize}
              minSize={rightMinSize}
              className="h-full min-h-0"
            >
              <RightSidebar onToggle={() => setOpen(false)} />
            </ResizablePanel>
          </>
        ) : null}
      </ResizablePanelGroup>

      {!open && (
        <button
          aria-label="Open right sidebar"
          title="Open right sidebar"
          onClick={() => setOpen(true)}
          className="absolute -right-2 top-1/2 z-20 -translate-y-1/2  rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent"
        >
          <ChevronLeft className="size-4 -translate-x-1" />
        </button>
      )}
    </div>
  );
};

export default MainWithRightSidebar;

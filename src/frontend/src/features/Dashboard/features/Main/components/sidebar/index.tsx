import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

export type SplitRightProps = {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultOpen?: boolean;
  rightDefaultSize?: number; // percentage
  rightMinSize?: number; // percentage
  className?: string;
};

const SplitRight: React.FC<SplitRightProps> = ({
  left,
  right,
  defaultOpen = true,
  rightDefaultSize = 25,
  rightMinSize = 15,
  className,
}) => {
  const [open, setOpen] = useState<boolean>(defaultOpen);

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
              <RightSidebar onToggle={() => setOpen(false)}>
                {right}
              </RightSidebar>
            </ResizablePanel>
          </>
        ) : null}
      </ResizablePanelGroup>

      {!open && (
        <button
          aria-label="Open right sidebar"
          title="Open right sidebar"
          onClick={() => setOpen(true)}
          className="absolute right-1 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 shadow hover:bg-accent"
        >
          <ChevronLeft className="size-4" />
        </button>
      )}
    </div>
  );
};

export const RightSidebar: React.FC<{
  children?: React.ReactNode;
  className?: string;
  onToggle?: () => void;
}> = ({ children, className, onToggle }) => {
  return (
    <aside
      className={`relative h-full w-full bg-white border-l shadow-sm flex flex-col ${
        className ?? ""
      }`}
    >
      {/* Edge-centered toggle */}
      {onToggle ? (
        <button
          onClick={onToggle}
          aria-label="Hide right sidebar"
          title="Hide right sidebar"
          className="absolute -left-3 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 shadow hover:bg-accent"
        >
          <ChevronRight className="size-4" />
        </button>
      ) : null}
      {children ?? <div>Right sidebar placeholder</div>}
    </aside>
  );
};

export { default as ConfigSidebarContent } from "./components/SidebarTabs";
export default SplitRight;

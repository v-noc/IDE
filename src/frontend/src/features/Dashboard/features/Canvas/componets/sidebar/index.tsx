import React, { useState } from "react";
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
            <ResizableHandle withHandle onDoubleClick={() => setOpen(false)} />
            <ResizablePanel
              defaultSize={rightDefaultSize}
              minSize={rightMinSize}
              className="h-full min-h-0"
            >
              {right}
            </ResizablePanel>
          </>
        ) : null}
      </ResizablePanelGroup>

      {!open && (
        <div
          aria-label="Open right sidebar"
          title="Open right sidebar"
          onClick={() => setOpen(true)}
          className="absolute right-0 top-0 h-full w-2 cursor-ew-resize z-10 hover:bg-border/50"
        />
      )}
    </div>
  );
};

export const RightSidebar: React.FC<{
  children?: React.ReactNode;
  className?: string;
}> = ({ children, className }) => {
  return (
    <aside
      className={`h-full w-full bg-white border-l shadow-sm flex flex-col ${
        className ?? ""
      }`}
    >
      {children ?? <div>Right sidebar placeholder</div>}
    </aside>
  );
};

export { default as ConfigSidebarContent } from "./components/SidebarTabs";
export default SplitRight;

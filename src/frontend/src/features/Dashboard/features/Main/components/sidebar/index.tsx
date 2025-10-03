import React from "react";
import { ChevronRight } from "lucide-react";
import CallSidebar from "./CallSidebar";
import {
  ResizableHandle,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Panel as ResizablePanel,
  type ImperativePanelHandle,
} from "react-resizable-panels";

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
      {onToggle ? (
        <button
          onClick={onToggle}
          aria-label="Hide right sidebar"
          title="Hide right sidebar"
          className="absolute -left-3 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent"
        >
          <ChevronRight className="size-4" />
        </button>
      ) : null}

      <ResizablePanelGroup direction="vertical" className="h-full min-h-0">
        <ResizablePanel collapsible defaultSize={65} minSize={35}>
          <div className="h-full min-h-0 overflow-auto">
            {children ?? (
              <div className="p-2 text-sm text-muted-foreground">
                Right sidebar placeholder
              </div>
            )}
          </div>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel collapsible defaultSize={35} minSize={20}>
          <div className="h-full min-h-0">
            <CallSidebar />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </aside>
  );
};

export { default as ConfigSidebarContent } from "./components/SidebarTabs";

import React, { useState } from "react";
import { ChevronRight, ChevronLeft } from "lucide-react";
import {
  ResizableHandle,
  ResizablePanelGroup,
  ResizablePanel,
} from "@/components/ui/resizable";
import ConfigSidebarContent from "./components/SidebarTabs";
import { RightSidebarTabs } from "./components/RightSidebarTabs";
import { useRightSidebarState } from "./hooks/useRightSidebarState";
import { useRightSidebarHandlers } from "./hooks/useRightSidebarHandlers";

export const RightSidebar: React.FC<{
  children: React.ReactNode;
  className?: string;
  defaultOpen?: boolean;
  rightDefaultSize?: number;
  rightMinSize?: number;
}> = ({
  children,
  className,
  defaultOpen = true,
  rightDefaultSize = 25,
  rightMinSize = 15,
}) => {
    const [isOpen, setIsOpen] = useState<boolean>(Boolean(defaultOpen));

    // 1. Data Layer
    const { initialBasicInfo, initialCustomization } = useRightSidebarState();

    // 2. Event Layer
    const { handleThemeChange, handleBasicInfoChange } = useRightSidebarHandlers();

    return (
      <div className={`relative h-full w-full min-h-0 overflow-hidden ${className ?? ""}`}>
        <ResizablePanelGroup direction="horizontal" className="h-full min-h-0">
          {/* Workspace Area */}
          <ResizablePanel
            defaultSize={isOpen ? 100 - rightDefaultSize : 100}
            minSize={40}
            className="h-full min-h-0"
          >
            {children}
          </ResizablePanel>

          {isOpen && (
            <>
              <ResizableHandle className="hover:bg-border/70 transition-colors bg-transparent border-l-1" />
              <ResizablePanel
                defaultSize={rightDefaultSize}
                minSize={rightMinSize}
                className="h-full min-h-0 group"
              >
                <aside className="relative h-full w-full bg-(--right-sidebar-color) border-l shadow-sm flex flex-col">
                  {/* Internal Close Button (visible on hover over the sidebar area) */}
                  <button
                    onClick={() => setIsOpen(false)}
                    aria-label="Hide right sidebar"
                    title="Hide right sidebar"
                    className="absolute group-hover:flex hidden -left-3 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent"
                  >
                    <ChevronRight className="size-4" />
                  </button>

                  <ResizablePanelGroup direction="vertical" className="h-full min-h-0">
                    {/* Top Section: Node Details / Form */}
                    <ResizablePanel collapsible defaultSize={65} minSize={35}>
                      <div className="h-full min-h-0 overflow-auto">
                        <ConfigSidebarContent
                          initialBasicInfo={initialBasicInfo}
                          initialCustomization={initialCustomization}
                          onChangeBasicInfo={handleBasicInfoChange}
                          onChangeCustomization={handleThemeChange}
                        />
                      </div>
                    </ResizablePanel>

                    <ResizableHandle
                      className="h-px bg-border shrink-0 border-t-2"
                      withHandle
                    />

                    {/* Bottom Section: Related content (Calls, Base Class) */}
                    <ResizablePanel collapsible defaultSize={35} minSize={20}>
                      <RightSidebarTabs />
                    </ResizablePanel>
                  </ResizablePanelGroup>
                </aside>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>

        {/* External Open Button (visible when sidebar is closed) */}
        {!isOpen && (
          <button
            aria-label="Open right sidebar"
            title="Open right sidebar"
            onClick={() => setIsOpen(true)}
            className="absolute -right-2 top-1/2 z-20 -translate-y-1/2 rounded-md border bg-background/80 p-1 py-2 shadow hover:bg-accent"
          >
            <ChevronLeft className="size-4 -translate-x-1" />
          </button>
        )}
      </div>
    );
  };

export { default as ConfigSidebarContent } from "./components/SidebarTabs";

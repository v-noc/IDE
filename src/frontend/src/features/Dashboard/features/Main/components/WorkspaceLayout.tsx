import React from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ChevronDown, ChevronUp } from "lucide-react";
import Sandbox from "./Sandbox";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import type { ProjectStore } from "@/features/Dashboard/store/useProjectStore";

interface WorkspaceLayoutProps {
  topPanelContent: React.ReactNode;
  rightSidebarContent?: React.ReactNode;
  tabId: string;
  floatingButton?: React.ReactNode;
  isSandboxOpen: boolean;
  onToggleSandbox: (open: boolean) => void;
  bottomPanelRef: React.RefObject<any>;
}

/**
 * Presentational component for the Workspace Layout.
 * Orchestrates the relationship between the main editor/docs area and the sandbox.
 */
export function WorkspaceLayout({
  topPanelContent,
  rightSidebarContent,
  tabId,
  floatingButton,
  isSandboxOpen,
  onToggleSandbox,
  bottomPanelRef,
}: WorkspaceLayoutProps) {
  const docSidebarSize = useProjectStore(
    (s: ProjectStore) => s.docSidebarSize[tabId],
  );
  const setDocSidebarSize = useProjectStore(
    (s: ProjectStore) => s.setDocSidebarSize,
  );

  const handleHorizontalLayout = (sizes: number[]) => {
    // When rightSidebarContent exists, sizes[0] is main content, sizes[1] is DocSidebar
    // We want to persist the DocSidebar size (index 1)
    if (rightSidebarContent && sizes.length > 1) {
      setDocSidebarSize(tabId, sizes[1]);
    }
  };

  // Calculate default sizes based on persisted state
  const mainContentDefaultSize = rightSidebarContent
    ? docSidebarSize
      ? 100 - docSidebarSize
      : 70
    : 100;
  const sidebarDefaultSize = docSidebarSize ?? 30;

  return (
    <div className="relative h-full w-full bg-(--background-color)">
      <ResizablePanelGroup
        direction="vertical"
        className="h-full min-h-0 relative"
      >
        <ResizablePanel
          defaultSize={70}
          minSize={40}
          className="flex flex-col border-b border-border bg-(--background-color)"
        >
          <ResizablePanelGroup
            direction="horizontal"
            className="h-full"
            onLayout={handleHorizontalLayout}
          >
            <ResizablePanel defaultSize={mainContentDefaultSize} minSize={30}>
              <div className="h-full w-full overflow-hidden">
                {topPanelContent}
              </div>
            </ResizablePanel>
            {rightSidebarContent && (
              <>
                <ResizableHandle className="w-1 bg-border" />
                <ResizablePanel defaultSize={sidebarDefaultSize} minSize={20}>
                  <div className="h-full w-full overflow-hidden">
                    {rightSidebarContent}
                  </div>
                </ResizablePanel>
              </>
            )}
          </ResizablePanelGroup>
        </ResizablePanel>

        <ResizableHandle className="bg-border" />

        <ResizablePanel
          ref={bottomPanelRef}
          defaultSize={30}
          minSize={16}
          collapsible
          className="relative rounded group"
        >
          <Sandbox tabId={tabId} />
          {/* Close button near the handle */}
          <button
            type="button"
            aria-label="Close sandbox"
            onClick={() => onToggleSandbox(false)}
            className="absolute -top-2 group-hover:flex hidden left-1/2 -translate-x-1/2 z-50 rounded-full border bg-background/90 px-4 py-1 text-xs shadow-sm hover:bg-accent"
          >
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Re-open toggle button when sandbox is hidden */}
      {!isSandboxOpen && (
        <button
          type="button"
          aria-label="Open sandbox"
          onClick={() => onToggleSandbox(true)}
          className="absolute bottom-2 left-1/2 -translate-x-1/2 z-50 rounded-full border border-border bg-card/90 px-2.5 py-1 text-xs text-foreground shadow-sm backdrop-blur hover:bg-card"
        >
          <ChevronUp className="h-3.5 w-3.5 inline-block mr-1 align-middle" />
          <span className="align-middle">Open sandbox</span>
        </button>
      )}
      {/* Floating button for additional actions */}
      {floatingButton}
    </div>
  );
}

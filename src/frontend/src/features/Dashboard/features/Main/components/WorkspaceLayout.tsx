import React from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { ChevronDown, ChevronUp } from "lucide-react";
import Sandbox from "./Sandbox";

interface WorkspaceLayoutProps {
  topPanelContent: React.ReactNode;
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
  isSandboxOpen,
  onToggleSandbox,
  bottomPanelRef,
}: WorkspaceLayoutProps) {
  return (
    <div className="relative h-full w-full bg-(--background-color)">
      <ResizablePanelGroup
        direction="vertical"
        className="h-full min-h-0 relative"
      >
        <ResizablePanel
          defaultSize={70}
          minSize={40}
          className="flex flex-col border-b bg-white"
        >
          <div className="flex-1 overflow-hidden">{topPanelContent}</div>
        </ResizablePanel>

        <ResizableHandle className="bg-border" />

        <ResizablePanel
          ref={bottomPanelRef}
          defaultSize={30}
          minSize={16}
          collapsible
          className="relative rounded group"
        >
          <Sandbox />
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
          className="absolute bottom-2 left-1/2 -translate-x-1/2 z-50 rounded-full border bg-white/90 px-2.5 py-1 text-xs shadow-sm backdrop-blur hover:bg-white"
        >
          <ChevronUp className="h-3.5 w-3.5 inline-block mr-1 align-middle" />
          <span className="align-middle">Open sandbox</span>
        </button>
      )}
    </div>
  );
}

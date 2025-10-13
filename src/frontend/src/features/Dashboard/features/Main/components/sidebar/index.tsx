import React from "react";
import { ChevronRight } from "lucide-react";
import CallSidebar from "./CallSidebar";
import {
  ResizableHandle,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Panel as ResizablePanel } from "react-resizable-panels";
import BaseClass from "./BaseClass";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
          <div className="h-full min-h-0 flex flex-col px-2 pt-2">
            <Tabs defaultValue="calls" className="flex-1 min-h-0 flex flex-col">
              <TabsList className="w-full">
                <TabsTrigger value="calls">Calls</TabsTrigger>
                <TabsTrigger value="base">Base Class</TabsTrigger>
              </TabsList>
              <TabsContent value="calls" className="flex-1 min-h-0">
                <CallSidebar hideHeader />
              </TabsContent>
              <TabsContent
                value="base"
                className="flex-1 min-h-0 overflow-auto px-1 py-2"
              >
                <BaseClass />
              </TabsContent>
            </Tabs>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </aside>
  );
};

export { default as ConfigSidebarContent } from "./components/SidebarTabs";

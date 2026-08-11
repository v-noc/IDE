import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import EditorCode from "./Code";
import { DocumentEditor } from "./Docs/DocumentEditor";
import Canvas from "./Canvas";
import { TasksBoard } from "@/features/Dashboard/features/Tasks";
import type { DocumentData } from "@/services/documents";

interface WorkspaceTabsProps {
  tabId: string;
  isCodeActive: boolean;
  tabValue: string;
  onTabValueChange: (value: string) => void;
  headerSlot: React.ReactNode;
  selectedDocument: DocumentData | null | undefined;
  nodeId?: string;
  projectId?: string;
  openTaskCount?: number;
  onNavigateToNode?: (nodeId: string) => void;
}

/**
 * Presentational component for the Workspace Tabs.
 * Manages the layout and content of the Code, Docs, and Canvas tabs.
 */
export function WorkspaceTabs({
  tabId,
  isCodeActive,
  tabValue,
  onTabValueChange,
  headerSlot,
  selectedDocument,
  nodeId,
  projectId = "",
  openTaskCount = 0,
  onNavigateToNode,
}: WorkspaceTabsProps) {
  return (
    <Tabs
      defaultValue={isCodeActive ? "code" : "docs"}
      value={tabValue}
      onValueChange={onTabValueChange}
      className="flex h-full w-full flex-col"
    >
      <TabsList className="rounded-none p-0 bg-(--background-color) text-muted-foreground w-full">
        {isCodeActive && (
          <TabsTrigger
            value="code"
            className="rounded-none bg-(--background-color) border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
          >
            Code
          </TabsTrigger>
        )}

        <TabsTrigger
          value="docs"
          className="rounded-none bg-(--background-color) border-x border-b border-border border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
        >
          Docs
        </TabsTrigger>
        <TabsTrigger
          value="canvas"
          className="rounded-none bg-(--background-color) border-x border-b border-border border-r-0 border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
        >
          Canvas
        </TabsTrigger>
        <TabsTrigger
          value="tasks"
          className="rounded-none bg-(--background-color) border-x border-b border-border border-r-0 border-t-2 border-t-transparent text-muted-foreground data-[state=active]:border-t-primary data-[state=active]:text-foreground data-[state=active]:shadow-none data-[state=active]:bg-transparent"
        >
          Tasks{openTaskCount > 0 ? ` ${openTaskCount}` : ""}
        </TabsTrigger>
        <div className="border-b border-border border-l h-full w-full"> </div>
      </TabsList>

      {headerSlot}

      {isCodeActive && (
        <TabsContent
          value="code"
          className="flex-1 flex flex-col overflow-hidden bg-(--background-color) border-t border-border p-0"
        >
          <div className="h-full w-full py-4 overflow-auto">
            <EditorCode tabId={tabId} />
          </div>
        </TabsContent>
      )}

      <TabsContent
        value="docs"
        className="flex flex-col overflow-hidden bg-(--background-color) border-t border-border"
      >
        <div className="flex-1 overflow-hidden py-2">
          <DocumentEditor
            key={selectedDocument?.id || "new"}
            document={selectedDocument || null}
            nodeId={nodeId ?? ""}
            projectId={projectId}
            autoSave={true}
            containerClassName="px-2 py-2"
          />
        </div>
      </TabsContent>
      <TabsContent
        value="canvas"
        className="flex flex-col overflow-hidden bg-(--background-color) border-t border-border"
      >
        <div className="flex-1 overflow-hidden">
          <div className="h-full w-full overflow-auto">
            <Canvas tabId={tabId} />
          </div>
        </div>
      </TabsContent>
      <TabsContent
        value="tasks"
        className="flex flex-col overflow-hidden bg-(--background-color) border-t border-border flex-1"
      >
        <TasksBoard
          projectId={projectId}
          tabId={tabId}
          onNavigateToNode={onNavigateToNode}
        />
      </TabsContent>
    </Tabs>
  );
}

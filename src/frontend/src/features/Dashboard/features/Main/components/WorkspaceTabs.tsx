import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import EditorCode from "./Code";
import Documents from "./Docs";
import Canvas from "./Canvas";

interface WorkspaceTabsProps {
    tabId: string;
    isCodeActive: boolean;
    tabValue: string;
    onTabValueChange: (value: string) => void;
    headerSlot: React.ReactNode;
    // Document props
    selectedDocument: any;
    nodeId?: string;
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
}: WorkspaceTabsProps) {
    return (
        <Tabs
            defaultValue={isCodeActive ? "code" : "docs"}
            value={tabValue}
            onValueChange={onTabValueChange}
            className="flex h-full w-full flex-col"
        >
            <TabsList className="rounded-none p-0 bg-white w-full">
                {isCodeActive && (
                    <TabsTrigger
                        value="code"
                        className="rounded-none bg-(--background-color) border border-border border-t-0 data-[state=active]:border-none data-[state=active]:shadow-none data-[state=active]:bg-transparent"
                    >
                        Code
                    </TabsTrigger>
                )}

                <TabsTrigger
                    value="docs"
                    className="rounded-none bg-(--background-color) border border-border border-t-0 data-[state=active]:border-none data-[state=active]:shadow-none data-[state=active]:bg-transparent"
                >
                    Docs
                </TabsTrigger>
                <TabsTrigger
                    value="canvas"
                    className="rounded-none bg-(--background-color) border border-border border-r-0 border-t-0 data-[state=active]:border-none data-[state=active]:shadow-none data-[state=active]:bg-transparent"
                >
                    Canvas
                </TabsTrigger>
                <div className="border-b border-border border-l h-full w-full"> </div>
            </TabsList>

            {headerSlot}

            {isCodeActive && (
                <TabsContent
                    value="code"
                    className="flex-1 flex flex-col overflow-hidden bg-white border-t p-0"
                >
                    <div className="h-full w-full py-4 overflow-auto">
                        <EditorCode tabId={tabId} />
                    </div>
                </TabsContent>
            )}

            <TabsContent
                value="docs"
                className="flex flex-col overflow-hidden bg-white border-t"
            >
                <div className="flex-1 overflow-hidden">
                    <div className="h-full pt-2 w-full overflow-auto">
                        <Documents
                            key={selectedDocument?._key || "new"}
                            document={
                                selectedDocument
                                    ? {
                                        id: selectedDocument._key,
                                        data: selectedDocument.data,
                                    }
                                    : undefined
                            }
                            nodeId={nodeId}
                        />
                    </div>
                </div>
            </TabsContent>
            <TabsContent
                value="canvas"
                className="flex flex-col overflow-hidden bg-white border-t"
            >
                <div className="flex-1 overflow-hidden">
                    <div className="h-full w-full overflow-auto">
                        <Canvas tabId={tabId} />
                    </div>
                </div>
            </TabsContent>
        </Tabs>
    );
}

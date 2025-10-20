import { useEffect, useMemo, useRef, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import useProjectStore from "../../store/useProjectStore";
import Documents from "./components/docs";
import EditorCode from "./components/code";
import Sandbox from "./components/sandbox";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import type { ImperativePanelHandle } from "react-resizable-panels";
import { ChevronDown, ChevronUp } from "lucide-react";

const MainCanvas = () => {
  const {
    selectedNode,
    secondarySelectedNode,
    setSelectedNode,
    setSecondarySelectedNode,
  } = useProjectStore();

  const effectiveNode = secondarySelectedNode ?? selectedNode;

  const { suffixName, displayPath } = useMemo(() => {
    const base = selectedNode?.qname?.replace(/\./g, " / ") ?? "";
    const hasSuffix = Boolean(
      secondarySelectedNode && secondarySelectedNode._key !== selectedNode?._key
    );
    const suffix = hasSuffix ? secondarySelectedNode?.name ?? "" : "";
    const display = hasSuffix ? (base ? `${base} / ${suffix}` : suffix) : base;
    return { suffixName: suffix, displayPath: display };
  }, [selectedNode?.qname, selectedNode?._key, secondarySelectedNode]);

  const isCodeActive = useMemo(() => {
    const t = effectiveNode?.node_type;
    return t === "function" || t === "class" || t === "file" || t === "call";
  }, [effectiveNode?.node_type]);

  const [isSandboxOpen, setIsSandboxOpen] = useState(true);
  const bottomPanelRef = useRef<ImperativePanelHandle>(null);

  // Sync panel collapsed state with our local boolean
  useEffect(() => {
    const panel = bottomPanelRef.current;
    if (!panel) return;
    if (isSandboxOpen && panel.isCollapsed()) {
      panel.expand();
    } else if (!isSandboxOpen && !panel.isCollapsed()) {
      panel.collapse();
    }
  }, [isSandboxOpen]);

  return (
    <div className="relative h-full w-full p-2">
      <ResizablePanelGroup
        direction="vertical"
        className="h-full min-h-0 relative"
      >
        <ResizablePanel defaultSize={70} minSize={40} className="flex flex-col">
          <div className="px-2 pb-2 text-xs text-muted-foreground truncate">
            {displayPath || "No selection"}
            {suffixName && (
              <>
                {" "}
                <button
                  type="button"
                  className="underline hover:no-underline cursor-pointer"
                  onClick={() => {
                    if (secondarySelectedNode) {
                      setSelectedNode(secondarySelectedNode);
                      setSecondarySelectedNode(null);
                    }
                  }}
                >
                  (promote)
                </button>
              </>
            )}
          </div>
          <div className="flex-1 overflow-hidden">
            <Tabs
              defaultValue={isCodeActive ? "code" : "docs"}
              className="flex h-full w-full flex-col bg-background rounded"
            >
              <TabsList>
                {isCodeActive && <TabsTrigger value="code">Code</TabsTrigger>}

                <TabsTrigger value="docs">Docs</TabsTrigger>
              </TabsList>

              {isCodeActive && (
                <TabsContent
                  value="code"
                  className="flex-1 flex flex-col overflow-hidden"
                >
                  <div className="h-full w-full overflow-auto py-4">
                    <EditorCode />
                  </div>
                </TabsContent>
              )}

              <TabsContent
                value="docs"
                className="flex flex-col overflow-hidden"
              >
                <div className="flex-1 rounded-md border overflow-hidden">
                  <div className="h-full w-full overflow-auto py-4">
                    <Documents />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </ResizablePanel>
        <ResizableHandle className="data-[panel-group-direction=vertical]:h-0.5 " />
        <ResizablePanel
          ref={bottomPanelRef}
          defaultSize={30}
          minSize={16}
          collapsible
          className="relative bg-background rounded"
        >
          <Sandbox />
          {/* Close button near the handle (bottom area, not side) */}
          <button
            type="button"
            aria-label="Close sandbox"
            onClick={() => setIsSandboxOpen(false)}
            className="absolute -top-2 left-1/2 -translate-x-1/2 z-50 rounded-full border bg-background/90 px-1.5 py-1 text-xs shadow-sm hover:bg-accent"
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
          onClick={() => setIsSandboxOpen(true)}
          className="absolute bottom-2 left-1/2 -translate-x-1/2 z-50 rounded-full border bg-white/90 px-2.5 py-1 text-xs shadow-sm backdrop-blur hover:bg-white"
        >
          <ChevronUp className="h-3.5 w-3.5 inline-block mr-1 align-middle" />
          <span className="align-middle">Open sandbox</span>
        </button>
      )}
    </div>
  );
};

export default MainCanvas;

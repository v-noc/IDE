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
    <div className="relative h-full w-full bg-[var(--background-color)]">
      <ResizablePanelGroup
        direction="vertical"
        className="h-full min-h-0 relative"
      >
        <ResizablePanel
          defaultSize={70}
          minSize={40}
          className="flex flex-col  border-b "
        >
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
              className="flex h-full w-full flex-col  "
            >
              <TabsList className="rounded-none p-0">
                {isCodeActive && (
                  <TabsTrigger value="code" className="rounded-none">
                    Code
                  </TabsTrigger>
                )}

                <TabsTrigger value="docs" className="rounded-none">
                  Docs
                </TabsTrigger>
              </TabsList>

              {isCodeActive && (
                <TabsContent
                  value="code"
                  className="flex-1 flex flex-col overflow-hidden bg-white border-t p-0"
                >
                  <div className="h-full w-full py-4 overflow-auto ">
                    <EditorCode />
                  </div>
                </TabsContent>
              )}

              <TabsContent
                value="docs"
                className="flex flex-col overflow-hidden bg-white border-t"
              >
                <div className="flex-1  pl-8  overflow-hidden">
                  <div className="h-full pt-2 w-full overflow-auto ">
                    <Documents />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </ResizablePanel>
        <ResizableHandle className="bg-transparent" />
        <ResizablePanel
          ref={bottomPanelRef}
          defaultSize={30}
          minSize={16}
          collapsible
          className="relative ] rounded"
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

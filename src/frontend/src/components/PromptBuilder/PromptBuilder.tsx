import { useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Dialog,
  DialogDescription,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type {
  ContainerNodeTree,
  AnyNodeTree,
  ProjectNodeTree,
} from "@/types/project";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";
import { findNodeByIdWithDescendantCache } from "@/features/Dashboard/utils/findNodeWithDescendantCache";
import { usePromptBuilder } from "./usePromptBuilder";
import TreePane from "./TreePane";
import SelectionDetailPane from "./SelectionDetailPane";
import PreviewPane from "./PreviewPane";
import { promptBuilderNodeKey } from "./nodeKey";

interface PromptBuilderProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  rootNode: ContainerNodeTree;
}

const PromptBuilder = ({
  open,
  onOpenChange,
  rootNode,
}: PromptBuilderProps) => {
  const queryClient = useQueryClient();
  const projectData = useProjectStore((s) => s.projectData);
  const projectKey = projectData?.id ?? "";
  const state = usePromptBuilder(rootNode);

  const selectedNode: AnyNodeTree | null = useMemo(() => {
    if (!state.selectedNodeKey) return null;
    const walk = (n: AnyNodeTree): AnyNodeTree | null => {
      if (promptBuilderNodeKey(n) === state.selectedNodeKey) return n;
      for (const c of (n.children ?? []) as AnyNodeTree[]) {
        const found = walk(c);
        if (found) return found;
      }
      return null;
    };
    const fromSubtree = walk(rootNode as AnyNodeTree);
    if (fromSubtree) return fromSubtree;
    return findNodeByIdWithDescendantCache(
      queryClient,
      projectData as ProjectNodeTree | null,
      projectKey,
      state.selectedNodeKey,
    );
  }, [state.selectedNodeKey, rootNode, queryClient, projectData, projectKey]);

  const xml = state.generateXml();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[80vh] w-full max-w-3xl flex-col overflow-hidden sm:max-w-5xl">
        <DialogHeader className="shrink-0 space-y-1 border-b border-border/60 px-6 pb-4 pt-6">
          <DialogTitle className="text-xl font-semibold tracking-tight">
            Prompt Builder
          </DialogTitle>
          <DialogDescription className="text-sm leading-relaxed text-muted-foreground">
            Select tree items, configure documents and code, then preview and
            copy your XML prompt.
          </DialogDescription>
        </DialogHeader>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-6 pb-6 pt-4">
          <Tabs defaultValue="builder" className="flex h-full min-h-0 flex-col gap-0">
            <TabsList className="mb-4 grid h-10 w-full max-w-sm grid-cols-2 gap-1 rounded-xl bg-muted/70 p-1 shadow-inner">
              <TabsTrigger
                value="builder"
                className="rounded-lg data-[state=active]:shadow-sm"
              >
                Builder
              </TabsTrigger>
              <TabsTrigger
                value="preview"
                className="rounded-lg data-[state=active]:shadow-sm"
              >
                Preview
              </TabsTrigger>
            </TabsList>

            <TabsContent
              value="builder"
              className="mt-0 grid min-h-0 flex-1 grid-cols-2 gap-4 data-[state=inactive]:hidden"
            >
              {/* Tree Pane */}
              <div className="flex min-h-0 flex-col overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950 shadow-sm">
                <div className="shrink-0 border-b border-zinc-800 bg-zinc-900 px-4 py-3">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">
                    Tree selection
                  </h3>
                </div>
                <div className="min-h-0 flex-1 overflow-auto bg-zinc-950">
                  <TreePane
                    root={rootNode}
                    checked={state.checked}
                    selectedNodeKey={state.selectedNodeKey}
                    onToggleChecked={state.toggleChecked}
                    onSelect={state.setSelectedNodeKey}
                    onLazyParentAccordionChange={
                      state.onLazyParentAccordionChange
                    }
                  />
                </div>
              </div>

              {/* Selection Detail Pane */}
              <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border border-border/70 bg-card shadow-sm">
                <div className="shrink-0 border-b border-border/60 bg-muted/30 px-4 py-3">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    Selection details
                  </h3>
                </div>
                <div className="min-h-0 flex-1 overflow-auto">
                  <div className="p-4">
                    <SelectionDetailPane
                      node={selectedNode}
                      checked={
                        !!(
                          selectedNode &&
                          state.checked[promptBuilderNodeKey(selectedNode)]
                        )
                      }
                      includeDocs={
                        !!(
                          selectedNode &&
                          state.includeDocs[promptBuilderNodeKey(selectedNode)]
                        )
                      }
                      includeCode={
                        !!(
                          selectedNode &&
                          state.includeCode[promptBuilderNodeKey(selectedNode)]
                        )
                      }
                      onToggleDocs={() =>
                        selectedNode &&
                        state.toggleIncludeDocs(
                          promptBuilderNodeKey(selectedNode),
                        )
                      }
                      onToggleCode={() =>
                        selectedNode &&
                        state.toggleIncludeCode(
                          promptBuilderNodeKey(selectedNode),
                        )
                      }
                      setDocumentsForNode={state.setDocumentsForNode}
                      setCodeForNode={state.setCodeForNode}
                    />
                  </div>
                </div>
              </div>
            </TabsContent>
            <TabsContent
              value="preview"
              className="mt-0 flex min-h-0 flex-1 flex-col data-[state=inactive]:hidden"
            >
              <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-xl border border-border/70 bg-card shadow-sm">
                <div className="shrink-0 border-b border-border/60 bg-muted/30 px-4 py-3">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    XML preview
                  </h3>
                </div>
                <div className="min-h-0 flex-1 overflow-auto">
                  <div className="p-4">
                    <PreviewPane xml={xml} />
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default PromptBuilder;

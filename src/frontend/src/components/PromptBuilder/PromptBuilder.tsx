import { useMemo } from "react";
import {
  Dialog,
  DialogDescription,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ContainerNodeTree, AnyNodeTree } from "@/types/project";
import { usePromptBuilder } from "./usePromptBuilder";
import TreePane from "./TreePane";
import SelectionDetailPane from "./SelectionDetailPane";
import PreviewPane from "./PreviewPane";

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
  const state = usePromptBuilder(rootNode);

  const selectedNode: AnyNodeTree | null = useMemo(() => {
    const walk = (n: AnyNodeTree): AnyNodeTree | null => {
      if (n._key === state.selectedNodeKey) return n;
      for (const c of (n.children ?? []) as AnyNodeTree[]) {
        const found = walk(c);
        if (found) return found;
      }
      return null;
    };
    return state.selectedNodeKey ? walk(rootNode as AnyNodeTree) : null;
  }, [state.selectedNodeKey, rootNode]);

  const xml = state.generateXml();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-full max-w-3xl sm:max-w-4xl h-[80vh]">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle>Prompt Builder</DialogTitle>
          <DialogDescription>
            Select tree items, configure documents and code, then preview and
            copy your XML prompt.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 min-h-0 overflow-hidden px-6 pb-6">
          <Tabs defaultValue="builder" className="h-full flex flex-col">
            <TabsList className="grid w-full max-w-xs grid-cols-2 mb-4">
              <TabsTrigger value="builder">Builder</TabsTrigger>
              <TabsTrigger value="preview">Preview</TabsTrigger>
            </TabsList>

            <TabsContent
              value="builder"
              className="flex-1 min-h-0 grid grid-cols-2 gap-4"
            >
              {/* Tree Pane */}
              <div className="border rounded-lg overflow-hidden bg-card">
                <div className="bg-muted/50 px-3 py-2 border-b">
                  <h3 className="text-xs font-semibold uppercase text-muted-foreground">
                    Tree Selection
                  </h3>
                </div>
                <div className="h-full overflow-auto">
                  <TreePane
                    root={rootNode}
                    checked={state.checked}
                    expanded={state.expanded}
                    selectedNodeKey={state.selectedNodeKey}
                    onToggleChecked={state.toggleChecked}
                    onToggleExpanded={state.toggleExpanded}
                    onSelect={state.setSelectedNodeKey}
                  />
                </div>
              </div>

              {/* Selection Detail Pane */}
              <div className="border rounded-lg overflow-hidden bg-card flex flex-col">
                <div className="bg-muted/50 px-3 py-2 border-b">
                  <h3 className="text-xs font-semibold uppercase text-muted-foreground">
                    Selection Details
                  </h3>
                </div>
                <div className="flex-1 min-h-0 overflow-auto">
                  <div className="p-3">
                    <SelectionDetailPane
                      node={selectedNode}
                      checked={
                        !!(selectedNode && state.checked[selectedNode._key])
                      }
                      includeDocs={
                        !!(selectedNode && state.includeDocs[selectedNode._key])
                      }
                      includeCode={
                        !!(selectedNode && state.includeCode[selectedNode._key])
                      }
                      onToggleDocs={() =>
                        selectedNode &&
                        state.toggleIncludeDocs(selectedNode._key)
                      }
                      onToggleCode={() =>
                        selectedNode &&
                        state.toggleIncludeCode(selectedNode._key)
                      }
                      setDocumentsForNode={state.setDocumentsForNode}
                      setCodeForNode={state.setCodeForNode}
                    />
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="preview" className="flex-1 min-h-0">
              <div className="border rounded-lg overflow-hidden bg-card h-full flex flex-col">
                <div className="bg-muted/50 px-3 py-2 border-b">
                  <h3 className="text-xs font-semibold uppercase text-muted-foreground">
                    XML Preview
                  </h3>
                </div>
                <div className="flex-1 min-h-0 overflow-auto">
                  <div className="p-3">
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

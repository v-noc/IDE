import { forwardRef, useImperativeHandle, useMemo } from "react";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import { usePlaygroundState } from "./hooks/usePlaygroundState";
import CodeEditor from "@/components/CodeEditor";
import SelectableList from "./components/SelectableList";
import {
  ResizablePanel,
  ResizablePanelGroup,
  ResizableHandle,
} from "@/components/ui/resizable";
import { PlusIcon } from "lucide-react";
import SettingsDialog from "./components/SettingsDialog";

export type PlayGroundHandle = {
  run: () => void;
  openSettings: () => void;
};

interface PlaygroundProps {
  onRunningChange?: (isRunning: boolean) => void;
}

/**
 * Playground Feature.
 * Orchestrates the code execution environment.
 */
const Playground = forwardRef<PlayGroundHandle, PlaygroundProps>(
  ({ onRunningChange }, ref) => {
    const {
      code,
      setCode,
      items,
      selectedId,
      setSelectedId,
      output,
      settingsOpen,
      setSettingsOpen,
      examplesPath,
      setExamplesPath,
      commandPrefix,
      setCommandPrefix,
      handleRun,
      handleAddSnippet,
      handleRemoveSnippet,
    } = usePlaygroundState(onRunningChange);

    const language = useMemo(() => detectLanguage("snippet.py"), []);

    useImperativeHandle(ref, () => ({
      run: handleRun,
      openSettings: () => setSettingsOpen(true),
    }));

    return (
      <div className="h-full w-full p-2 flex flex-col">
        <ResizablePanelGroup
          direction="horizontal"
          className="h-[calc(100%-1rem)] py-1"
        >
          <ResizablePanel defaultSize={20} minSize={16}>
            <div className="flex h-full flex-col gap-2 pr-2 rounded p-2 border bg-white">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="text-sm font-medium text-muted-foreground">Files</div>
                <button
                  type="button"
                  onClick={handleAddSnippet}
                  className="h-6 w-6 rounded border text-xs leading-6 flex justify-center items-center hover:bg-accent"
                >
                  <PlusIcon size={15} />
                </button>
              </div>
              <SelectableList
                items={items}
                selectedId={selectedId}
                onSelect={setSelectedId}
                onRemove={handleRemoveSnippet}
                isItemRemovable={(item) => item.id !== "playground"}
              />
            </div>
          </ResizablePanel>

          <ResizableHandle withHandle className="w-3 bg-transparent" />

          <ResizablePanel defaultSize={80} minSize={40}>
            <ResizablePanelGroup direction="horizontal" className="h-full">
              <ResizablePanel
                defaultSize={60}
                minSize={40}
                className="rounded p-2 px-0 border bg-white"
              >
                <div className="h-full overflow-auto">
                  <CodeEditor
                    language={language}
                    value={code}
                    onChange={(v) => setCode(v ?? "")}
                  />
                </div>
              </ResizablePanel>

              <ResizableHandle withHandle className="w-3 bg-transparent" />

              <ResizablePanel defaultSize={40} minSize={20}>
                <div className="h-full border bg-white rounded p-2 flex flex-col overflow-hidden">
                  <div className="mb-2 text-sm font-medium text-muted-foreground">Output</div>
                  <pre className="flex-grow min-h-0 overflow-y-auto whitespace-break-spaces rounded border bg-muted/40 p-2 text-xs font-mono">
                    {output}
                  </pre>
                </div>
              </ResizablePanel>
            </ResizablePanelGroup>
          </ResizablePanel>
        </ResizablePanelGroup>

        <SettingsDialog
          open={settingsOpen}
          onOpenChange={setSettingsOpen}
          examplesPath={examplesPath}
          commandPrefix={commandPrefix}
          onChangeExamplesPath={setExamplesPath}
          onChangeCommandPrefix={setCommandPrefix}
        />
      </div>
    );
  }
);

Playground.displayName = "Playground";
export default Playground;

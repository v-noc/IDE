import CodeEditor from "@/components/CodeEditor";
import { forwardRef, useImperativeHandle, useMemo, useState } from "react";
import SelectableList, { type SelectableItem } from "../SelectableList";
import {
  ResizablePanel,
  ResizablePanelGroup,
  ResizableHandle,
} from "@/components/ui/resizable";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import SettingsDialog from "../SettingsDialog";
import { PlusIcon } from "lucide-react";
import { useRunCode } from "@/features/Dashboard/features/Main/hooks/usePlayGround";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

export type PlayGroundHandle = {
  run: () => void;
  openSettings: () => void;
};

interface PlayGroundProps {
  onRunningChange?: (isRunning: boolean) => void;
}

const PlayGround = forwardRef<PlayGroundHandle, PlayGroundProps>(
  ({ onRunningChange }, ref) => {
    const [code, setCode] = useState("# write your code here");
    const fileName = "snippet.py";
    const [items, setItems] = useState<SelectableItem[]>([
      { id: "playground", label: "Playground" },
    ]);
    const [selectedId, setSelectedId] = useState<string | undefined>(
      "playground"
    );
    const [output, setOutput] = useState<string>("");
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [examplesPath, setExamplesPath] = useState("");
    const [commandPrefix, setCommandPrefix] = useState("python");
    const project = useProjectStore((s) => s.projectData);
    const runCode = useRunCode(project?._key);

    const language = useMemo(() => detectLanguage(fileName), [fileName]);

    const handleRun = async () => {
      onRunningChange?.(true);
      const relativeFile =
        selectedId === "playground" ? "playground.py" : `${selectedId}.py`;
      const fullPath = `${examplesPath}/${relativeFile}`;
      const runCommand = `${commandPrefix} ${fullPath}`;
      setOutput(`Command: ${runCommand}`);
      try {
        const resp = await runCode.mutateAsync({
          code,
          executable_path: null,
          examples_path: examplesPath,
          command_prefix: commandPrefix,
          filename: relativeFile,
        });
        setOutput((prev) => `${prev}\n${resp.response}`);
      } catch {
        setOutput((prev) => `${prev}\nError running code`);
      } finally {
        onRunningChange?.(false);
      }
    };

    useImperativeHandle(ref, () => ({
      run: handleRun,
      openSettings: () => setSettingsOpen(true),
    }));

    const handleSelect = (id: string) => setSelectedId(id);
    const handleRemove = (id: string) => {
      if (id === "playground") return;
      setItems((prev) => prev.filter((x) => x.id !== id));
      if (selectedId === id) setSelectedId("playground");
    };
    const handleAdd = () => {
      const newId = `snippet-${Math.random().toString(36).slice(2, 8)}`;
      const newItem = { id: newId, label: `Snippet ${items.length}` };
      setItems((prev) => [...prev, newItem]);
      setSelectedId(newId);
    };

    return (
      <div className="h-full w-full  p-2 flex flex-col">
        <ResizablePanelGroup
          direction="horizontal"
          className="h-[calc(100%-2rem)] py-1"
        >
          <ResizablePanel defaultSize={20} minSize={16}>
            <div className="flex h-full flex-col gap-2 pr-2 rounded p-2 border bg-white">
              <div className="flex items-center justify-between border-b pb-2">
                <div className="text-sm font-medium text-muted-foreground">
                  Files
                </div>
                <button
                  type="button"
                  onClick={handleAdd}
                  className="h-6 w-6 rounded border text-xs leading-6 flex justify-center items-center hover:bg-accent"
                  aria-label="Add snippet"
                  title="Add snippet"
                >
                  <PlusIcon size={15} />
                </button>
              </div>
              <SelectableList
                items={items}
                selectedId={selectedId}
                onSelect={handleSelect}
                onRemove={handleRemove}
                isItemRemovable={(item) => item.id !== "playground"}
              />
            </div>
          </ResizablePanel>
          <ResizableHandle withHandle className="w-3 bg-transparent" />
          <ResizablePanel defaultSize={80} minSize={40}>
            <ResizablePanelGroup direction="horizontal" className="h-full ">
              <ResizablePanel
                defaultSize={60}
                minSize={40}
                className="rounded p-2 px-0 border bg-white"
              >
                <div className="h-full overflow-auto ">
                  <CodeEditor
                    language={language}
                    value={code}
                    onChange={(value) => setCode(value ?? "")}
                  />
                </div>
              </ResizablePanel>
              <ResizableHandle withHandle className="w-3 bg-transparent" />
              <ResizablePanel defaultSize={40} minSize={20}>
                {/* This is the parent container for the output panel */}
                <div className="h-full border bg-white rounded p-2 flex flex-col overflow-hidden">
                  {/* 1. This label stays fixed at the top */}
                  <div className="mb-2 text-sm font-medium text-muted-foreground">
                    Output
                  </div>

                  {/* 2. The <pre> tag now uses flex-1 and min-h-0 for proper scrolling */}
                  <pre className="flex-grow min-h-0 overflow-y-auto whitespace-break-spaces rounded border bg-muted/40 p-2 text-xs">
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

export default PlayGround;

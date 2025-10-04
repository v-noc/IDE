import CodeEditor from "@/components/CodeEditor";
import { useMemo, useState } from "react";
import RunToolbar from "../components/RunToolbar";
import SelectableList, {
  type SelectableItem,
} from "../components/SelectableList";
import {
  ResizablePanel,
  ResizablePanelGroup,
  ResizableHandle,
} from "@/components/ui/resizable";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";

const PlayGround = () => {
  const [code, setCode] = useState("");
  const fileName = "snippet.py";
  const [isRunning, setIsRunning] = useState(false);
  const [items, setItems] = useState<SelectableItem[]>([
    { id: "playground", label: "Playground" },
  ]);
  const [selectedId, setSelectedId] = useState<string | undefined>(
    "playground"
  );
  const [output, setOutput] = useState<string>("");

  const language = useMemo(() => detectLanguage(fileName), [fileName]);

  const handleRun = async () => {
    setIsRunning(true);
    try {
      // Placeholder: run logic can be integrated with backend later
      await new Promise((r) => setTimeout(r, 800));
      setOutput(
        `Executed at ${new Date().toLocaleTimeString()}\n\n${
          code ? code : "# (no code)"
        }`
      );
    } finally {
      setIsRunning(false);
    }
  };

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
    <div className="h-full w-full rounded border p-2 flex flex-col">
      <RunToolbar onRun={handleRun} isRunning={isRunning} className="mb-2" />
      <ResizablePanelGroup
        direction="horizontal"
        className="h-[calc(100%-2rem)]"
      >
        <ResizablePanel defaultSize={20} minSize={16}>
          <div className="flex h-full flex-col gap-2 pr-2 border-r">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-muted-foreground">
                Files
              </div>
              <button
                type="button"
                onClick={handleAdd}
                className="h-6 w-6 rounded border text-xs leading-6 text-center hover:bg-accent"
                aria-label="Add snippet"
                title="Add snippet"
              >
                +
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
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={80} minSize={40}>
          <ResizablePanelGroup direction="horizontal" className="h-full">
            <ResizablePanel defaultSize={60} minSize={40}>
              <div className="h-full overflow-auto">
                <CodeEditor
                  language={language}
                  value={code}
                  onChange={(value) => setCode(value ?? "")}
                />
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={40} minSize={20}>
              <div className="h-full border-l p-2">
                <div className="mb-2 text-sm font-medium text-muted-foreground">
                  Output
                </div>
                <pre className="h-full w-full overflow-auto rounded border bg-muted/40 p-2 text-xs">
                  {output}
                </pre>
              </div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
};

export default PlayGround;

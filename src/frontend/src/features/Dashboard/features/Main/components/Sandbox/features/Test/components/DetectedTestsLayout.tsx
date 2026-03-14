import { useMemo } from "react";
import CodeEditor from "@/components/CodeEditor";
import { detectLanguage } from "@/components/CodeEditor/detectLanguage";
import { Button } from "@/components/ui/button";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import type { TestCaseItem } from "../types";

interface DetectedTestsLayoutProps {
  testCases: TestCaseItem[];
  selectedTestId: string;
  targetFunctionCode: string;
  onSelectTest: (id: string) => void;
  onBackToEmptyState: () => void;
}

export default function DetectedTestsLayout({
  testCases,
  selectedTestId,
  targetFunctionCode,
  onSelectTest,
  onBackToEmptyState,
}: DetectedTestsLayoutProps) {
  const language = useMemo(() => detectLanguage("target_function.py"), []);

  return (
    <div className="h-full w-full p-1">
      <ResizablePanelGroup direction="horizontal" className="h-full">
        <ResizablePanel defaultSize={25} minSize={18}>
          <div className="h-full rounded-lg border bg-white p-3 flex flex-col">
            <div className="border-b pb-2 mb-2">
              <div className="text-sm font-semibold text-slate-800">Detected test cases</div>
              <p className="text-xs text-muted-foreground mt-1">
                Select a test to preview related code context.
              </p>
            </div>

            <div className="space-y-2 overflow-y-auto">
              {testCases.map((testCase) => {
                const isSelected = testCase.id === selectedTestId;
                return (
                  <button
                    key={testCase.id}
                    type="button"
                    onClick={() => onSelectTest(testCase.id)}
                    className={`w-full rounded border px-3 py-2 text-left transition-colors ${
                      isSelected
                        ? "border-primary bg-accent/50"
                        : "border-slate-200 hover:bg-accent/30"
                    }`}
                  >
                    <div className="text-sm font-medium text-slate-800 truncate">
                      {testCase.name}
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-1 uppercase tracking-wide">
                      {testCase.status}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle className="w-3 bg-transparent" />

        <ResizablePanel defaultSize={75} minSize={45}>
          <div className="h-full rounded-lg border bg-white p-2 flex flex-col">
            <div className="border-b px-2 pb-2 mb-2 flex items-center justify-between gap-2">
              <div>
                <div className="text-sm font-semibold text-slate-800">Target function code</div>
                <p className="text-xs text-muted-foreground">
                  Mock preview from <code>target_function</code> (integration pending).
                </p>
              </div>
              <Button size="sm" variant="outline" onClick={onBackToEmptyState}>
                Back to empty state
              </Button>
            </div>

            <div className="flex-1 min-h-0 overflow-hidden">
              <CodeEditor
                language={language}
                value={targetFunctionCode}
                options={{ readOnly: true }}
              />
            </div>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

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
  testCode: string;
  testCodePath: string;
  testCodeTitle: string;
  testCodeSubtitle: string;
  isTestCodeLoading?: boolean;
  isTestCodeError?: boolean;
  onSelectTest: (id: string) => void;
  onBackToEmptyState: () => void;
}

export default function DetectedTestsLayout({
  testCases,
  selectedTestId,
  testCode,
  testCodePath,
  testCodeTitle,
  testCodeSubtitle,
  isTestCodeLoading = false,
  isTestCodeError = false,
  onSelectTest,
  onBackToEmptyState,
}: DetectedTestsLayoutProps) {
  const language = useMemo(
    () => detectLanguage(testCodePath || "test_case.py"),
    [testCodePath],
  );

  return (
    <div className="h-full w-full p-1">
      <ResizablePanelGroup direction="horizontal" className="h-full">
        <ResizablePanel defaultSize={25} minSize={18}>
          <div className="h-full rounded-lg border border-border bg-card p-3 flex flex-col">
            <div className="border-b pb-2 mb-2">
              <div className="text-sm font-semibold text-slate-800">
                Detected test cases
              </div>
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
                    {testCase.description ? (
                      <div className="text-[11px] text-muted-foreground mt-1 line-clamp-2">
                        {testCase.description}
                      </div>
                    ) : null}
                  </button>
                );
              })}
            </div>
          </div>
        </ResizablePanel>

        <ResizableHandle withHandle className="w-3 bg-transparent" />

        <ResizablePanel defaultSize={75} minSize={45}>
          <div className="h-full rounded-lg border border-border bg-card p-2 flex flex-col">
            <div className="border-b px-2 pb-2 mb-2 flex items-center justify-between gap-2">
              <div>
                <div className="text-sm font-semibold text-slate-800">
                  {testCodeTitle || "Test code"}
                </div>
                {testCodeSubtitle ? (
                  <p className="text-xs text-muted-foreground">
                    {testCodeSubtitle}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="flex-1 min-h-0 overflow-hidden">
              <CodeEditor
                language={language}
                value={testCode}
                isLoading={isTestCodeLoading}
                isError={isTestCodeError}
                options={{ readOnly: true }}
              />
            </div>
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}

import { forwardRef, useEffect, useImperativeHandle, useState } from "react";
import { useParams } from "react-router";
import {
  useCreateTestConfig,
  type RunTestsResponse,
  useTestConfig,
  useUpdateTestConfig,
} from "@/services/tests";
import { toast } from "sonner";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import ConfigNotCreatedState from "./components/ConfigNotCreatedState";
import DetectedTestsLayout from "./components/DetectedTestsLayout";
import NoTestCasesState from "./components/NoTestCasesState";
import TestConfigDialog from "./components/TestConfigDialog";
import { MOCK_TARGET_FUNCTION_CODE, MOCK_TEST_CASES } from "./mocks";
import type { TestConfig, TestViewState } from "./types";
import { useRunAllTests } from "./hooks/useRunAllTests";

export type TestHandle = {
  run: () => void;
  openSettings: () => void;
};

interface TestProps {
  onRunningChange?: (isRunning: boolean) => void;
  onConfigChange?: (isConfigCreated: boolean) => void;
}

const DEFAULT_CONFIG: TestConfig = {
  enabled: true,
  testRoot: "src/backend/tests",
  testArgs: "",
  executablePath: "",
};

const Test = forwardRef<TestHandle, TestProps>(
  ({ onRunningChange, onConfigChange }, ref) => {
    const { projectId } = useParams();
    const projectNodeId = projectId ? `ProjectSchema/${projectId}` : "";
    const [viewState, setViewState] = useState<TestViewState>("empty_tests");
    const [selectedTestId, setSelectedTestId] = useState<string>(
      MOCK_TEST_CASES[0].id,
    );
    const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
    const [testConfig, setTestConfig] = useState<TestConfig>(DEFAULT_CONFIG);
    const [latestRunResult, setLatestRunResult] =
      useState<RunTestsResponse | null>(null);
    const [isResultPanelOpen, setIsResultPanelOpen] = useState(false);

    const {
      data: configData,
      isLoading: isConfigLoading,
      error: configError,
    } = useTestConfig(projectNodeId);
    const createConfigMutation = useCreateTestConfig(projectNodeId);
    const updateConfigMutation = useUpdateTestConfig(projectNodeId);
    const { runAllTests, isRunning } = useRunAllTests(projectNodeId);
    const isConfigCreated = Boolean(configData);

    const isConfigMissing =
      !isConfigLoading &&
      !configData &&
      typeof configError === "object" &&
      configError !== null &&
      "status" in configError &&
      (configError as { status?: number }).status === 404;

    const handleOpenSettings = () => {
      setIsConfigDialogOpen(true);
    };

    const handleSaveConfiguration = async () => {
      if (!projectNodeId) return;

      const payload = {
        enabled: testConfig.enabled,
        test_root: testConfig.testRoot,
        test_args: testConfig.testArgs,
        executable_path: testConfig.executablePath,
      };

      if (isConfigCreated) {
        await updateConfigMutation.mutateAsync(payload);
      } else {
        await createConfigMutation.mutateAsync(payload);
      }

      setIsConfigDialogOpen(false);
      setViewState("empty_tests");
    };

    const handleRunTests = async () => {
      if (!isConfigCreated) {
        setIsConfigDialogOpen(true);
        return;
      }

      if (isRunning) return;

      try {
        const runResult = await runAllTests();
        setLatestRunResult(runResult);
        setIsResultPanelOpen(true);
        const runError =
          runResult.run?.error_message ??
          runResult.runs.find((item) => item.error_message)?.error_message;
        if (runError) {
          toast.error(runError);
          setViewState("empty_tests");
          return;
        }
        if (runResult.total_test_cases > 0 || runResult.total_test_links > 0) {
          setViewState("detected_tests");
          return;
        }

        setViewState("empty_tests");
      } catch {
        toast.error("Failed to run tests.");
      }
    };

    useImperativeHandle(ref, () => ({
      run: () => {
        void handleRunTests();
      },
      openSettings: handleOpenSettings,
    }));

    useEffect(() => {
      onRunningChange?.(isRunning);
    }, [isRunning, onRunningChange]);

    useEffect(() => {
      if (!configData) return;
      setTestConfig({
        enabled: configData.enabled,
        testRoot: configData.test_root,
        testArgs: configData.test_args,
        executablePath: configData.executable_path ?? "",
      });
      setViewState((prev) =>
        prev === "missing_config" ? "empty_tests" : prev,
      );
    }, [configData]);

    useEffect(() => {
      onConfigChange?.(isConfigCreated);
    }, [isConfigCreated, onConfigChange]);

    useEffect(() => {
      if (isConfigMissing) {
        setViewState("missing_config");
      }
    }, [isConfigMissing]);

    if (isConfigLoading) {
      return (
        <div className="h-full w-full rounded-lg border bg-white p-8 flex items-center justify-center text-sm text-muted-foreground">
          Loading test configuration...
        </div>
      );
    }

    let content = (
      <DetectedTestsLayout
        testCases={MOCK_TEST_CASES}
        selectedTestId={selectedTestId}
        targetFunctionCode={MOCK_TARGET_FUNCTION_CODE}
        onSelectTest={setSelectedTestId}
        onBackToEmptyState={() => setViewState("empty_tests")}
      />
    );

    if (viewState === "missing_config") {
      content = (
        <ConfigNotCreatedState onCreateConfiguration={handleOpenSettings} />
      );
    } else if (viewState === "empty_tests") {
      content = (
        <NoTestCasesState onCreateTest={() => {}} onRunTests={handleRunTests} />
      );
    }

    const latestRawOutput = latestRunResult
      ? latestRunResult.runs
          .map((run, index) => {
            if (!run.raw_output) return null;
            return latestRunResult.runs.length > 1
              ? `--- Run ${index + 1} ---\n${run.raw_output}`
              : run.raw_output;
          })
          .filter(Boolean)
          .join("\n\n")
      : "";

    return (
      <>
        <div className="h-full w-full flex min-w-0 gap-1">
          <div className="flex-1 min-w-0 flex flex-col gap-2">
            {latestRunResult && !isResultPanelOpen && (
              <div className="flex justify-end px-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsResultPanelOpen(true)}
                >
                  Show output
                </Button>
              </div>
            )}
            <div className="flex-1 min-h-0">{content}</div>
          </div>

          {latestRunResult && isResultPanelOpen && (
            <aside className="w-[45%] shrink-0 rounded-lg border bg-white flex flex-col">
              <div className="px-3 py-2 border-b flex items-center justify-between">
                <div className="text-sm font-semibold text-slate-800">
                  Output
                </div>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={() => setIsResultPanelOpen(false)}
                >
                  <X className="size-4" />
                </Button>
              </div>

              <ScrollArea className="flex-1">
                <div className="p-3">
                  <pre className="text-xs whitespace-pre-wrap wrap-break-word">
                    {latestRawOutput || "No subprocess output from last run."}
                  </pre>
                </div>
              </ScrollArea>
            </aside>
          )}
        </div>

        <TestConfigDialog
          open={isConfigDialogOpen}
          onOpenChange={setIsConfigDialogOpen}
          config={testConfig}
          isConfigCreated={isConfigCreated}
          onChangeConfig={setTestConfig}
          onSave={() => {
            void handleSaveConfiguration();
          }}
        />
      </>
    );
  },
);

Test.displayName = "Test";

export default Test;

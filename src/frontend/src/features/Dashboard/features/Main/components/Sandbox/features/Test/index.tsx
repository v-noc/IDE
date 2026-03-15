import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { useParams } from "react-router";
import {
  useCreateTestConfig,
  useTestConfig,
  useUpdateTestConfig,
} from "@/services/tests";
import ConfigNotCreatedState from "./components/ConfigNotCreatedState";
import DetectedTestsLayout from "./components/DetectedTestsLayout";
import NoTestCasesState from "./components/NoTestCasesState";
import TestConfigDialog from "./components/TestConfigDialog";
import { MOCK_TARGET_FUNCTION_CODE, MOCK_TEST_CASES } from "./mocks";
import type { TestConfig, TestViewState } from "./types";

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
};

const Test = forwardRef<TestHandle, TestProps>(
  ({ onRunningChange, onConfigChange }, ref) => {
  const { projectId } = useParams();
  const projectNodeId = projectId ? `ProjectSchema/${projectId}` : "";
  const [viewState, setViewState] = useState<TestViewState>("empty_tests");
  const [selectedTestId, setSelectedTestId] = useState<string>(
    MOCK_TEST_CASES[0].id,
  );
  const [isRunning, setIsRunning] = useState(false);
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
  const [testConfig, setTestConfig] = useState<TestConfig>(DEFAULT_CONFIG);
  const runTimeoutRef = useRef<number | null>(null);
  const {
    data: configData,
    isLoading: isConfigLoading,
    error: configError,
  } = useTestConfig(projectNodeId);
  const createConfigMutation = useCreateTestConfig(projectNodeId);
  const updateConfigMutation = useUpdateTestConfig(projectNodeId);
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
    };

    if (isConfigCreated) {
      await updateConfigMutation.mutateAsync(payload);
    } else {
      await createConfigMutation.mutateAsync(payload);
    }

    setIsConfigDialogOpen(false);
    setViewState("empty_tests");
  };

  const handleRunTests = () => {
    if (!isConfigCreated) {
      setIsConfigDialogOpen(true);
      return;
    }

    if (isRunning) return;

    setIsRunning(true);
    runTimeoutRef.current = window.setTimeout(() => {
      setIsRunning(false);
      if (viewState === "empty_tests") {
        setViewState("detected_tests");
      }
    }, 900);
  };

  useImperativeHandle(ref, () => ({
    run: handleRunTests,
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
    });
    setViewState((prev) => (prev === "missing_config" ? "empty_tests" : prev));
  }, [configData]);

  useEffect(() => {
    onConfigChange?.(isConfigCreated);
  }, [isConfigCreated, onConfigChange]);

  useEffect(() => {
    if (isConfigMissing) {
      setViewState("missing_config");
    }
  }, [isConfigMissing]);

  useEffect(() => {
    return () => {
      if (runTimeoutRef.current) {
        window.clearTimeout(runTimeoutRef.current);
      }
    };
  }, []);

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

  return (
    <>
      {content}

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

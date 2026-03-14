import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
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
}

const DEFAULT_CONFIG: TestConfig = {
  framework: "pytest",
  testsPath: "src/backend/tests",
  commandPrefix: "python -m",
};

const Test = forwardRef<TestHandle, TestProps>(({ onRunningChange }, ref) => {
  const [viewState, setViewState] = useState<TestViewState>("missing_config");
  const [selectedTestId, setSelectedTestId] = useState<string>(MOCK_TEST_CASES[0].id);
  const [isRunning, setIsRunning] = useState(false);
  const [isConfigDialogOpen, setIsConfigDialogOpen] = useState(false);
  const [isConfigCreated, setIsConfigCreated] = useState(false);
  const [testConfig, setTestConfig] = useState<TestConfig>(DEFAULT_CONFIG);
  const runTimeoutRef = useRef<number | null>(null);

  const handleOpenSettings = () => {
    setIsConfigDialogOpen(true);
  };

  const handleSaveConfiguration = () => {
    setIsConfigCreated(true);
    setIsConfigDialogOpen(false);
    if (viewState === "missing_config") {
      setViewState("empty_tests");
    }
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
    return () => {
      if (runTimeoutRef.current) {
        window.clearTimeout(runTimeoutRef.current);
      }
    };
  }, []);

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
    content = <ConfigNotCreatedState onCreateConfiguration={handleOpenSettings} />;
  } else if (viewState === "empty_tests") {
    content = (
      <NoTestCasesState
        onCreateTest={() => {}}
        onRunTests={handleRunTests}
        onLoadMockDetectedTests={() => setViewState("detected_tests")}
      />
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
        onSave={handleSaveConfiguration}
      />
    </>
  );
});

Test.displayName = "Test";

export default Test;

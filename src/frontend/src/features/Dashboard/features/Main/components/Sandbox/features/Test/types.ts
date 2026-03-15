export interface TestCaseItem {
  id: string;
  name: string;
  description: string;
  nodeId: string;
  path: string;
  targetFunctionId: string | null;
  targetFunctionName: string;
  targetFunctionDescription: string;
}

export type TestViewState = "missing_config" | "empty_tests" | "detected_tests";

export interface TestConfig {
  enabled: boolean;
  testRoot: string;
  testArgs: string;
  executablePath: string;
}

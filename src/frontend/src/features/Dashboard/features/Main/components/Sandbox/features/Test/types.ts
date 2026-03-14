export type TestCaseStatus = "ready" | "draft";

export interface TestCaseItem {
  id: string;
  name: string;
  status: TestCaseStatus;
}

export type TestViewState = "missing_config" | "empty_tests" | "detected_tests";

export interface TestConfig {
  framework: string;
  testsPath: string;
  commandPrefix: string;
}

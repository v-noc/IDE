export type TestCaseStatus = "ready" | "draft";

export interface TestCaseItem {
  id: string;
  name: string;
  status: TestCaseStatus;
}

export type TestViewState = "missing_config" | "empty_tests" | "detected_tests";

export interface TestConfig {
  enabled: boolean;
  testRoot: string;
  testArgs: string;
}

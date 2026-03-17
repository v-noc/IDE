import type { TestCaseItem } from "./types";

export const MOCK_TEST_CASES: TestCaseItem[] = [
  { id: "t1", name: "test_handles_valid_user_input", status: "ready" },
  { id: "t2", name: "test_returns_400_for_invalid_payload", status: "ready" },
  { id: "t3", name: "test_retries_when_service_unavailable", status: "draft" },
];

export const MOCK_TARGET_FUNCTION_CODE = `def create_test_case(payload: dict) -> dict:
    name = payload.get("name", "").strip()
    if not name:
        raise ValueError("name is required")

    return {
        "id": "mock-id-001",
        "name": name,
        "status": "ready",
    }
`;

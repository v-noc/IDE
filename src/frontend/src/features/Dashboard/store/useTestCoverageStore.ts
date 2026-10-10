import { create } from "zustand";

interface ActiveCoverage {
  nodeId: string;
  lines: number[];
}

interface TestCoverageState {
  /** The node whose test coverage should be highlightable, per tab — set only while a test case is selected in the Test panel. */
  active: Record<string, ActiveCoverage | null>;
  setActiveCoverage: (tabId: string, coverage: ActiveCoverage | null) => void;
}

const EMPTY_LINES: number[] = [];

const useTestCoverageStore = create<TestCoverageState>((set) => ({
  active: {},
  setActiveCoverage: (tabId, coverage) =>
    set((state) => ({ active: { ...state.active, [tabId]: coverage } })),
}));

/** Covered lines for `nodeId`, but only when it's the node currently selected in the Test panel for `tabId`. */
export function useActiveCoverageForNode(
  tabId: string,
  nodeId: string,
): number[] {
  return useTestCoverageStore((s) => {
    const active = s.active[tabId];
    return active && nodeId && active.nodeId === nodeId
      ? active.lines
      : EMPTY_LINES;
  });
}

export default useTestCoverageStore;

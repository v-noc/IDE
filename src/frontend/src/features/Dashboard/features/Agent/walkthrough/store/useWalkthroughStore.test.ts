import { beforeEach, describe, expect, it, vi } from "vitest";
import smallFunctionFixture from "../fixtures/smallFunction.json";
import { applyFrame } from "../source/applyFrame";
import { mockFixtureSchema } from "../types";
import { flattenSession } from "./flatten";
import { isCurrentStepNode, useWalkthroughStore } from "./useWalkthroughStore";

vi.mock("@/features/Dashboard/store/useTabStore", () => ({
  default: {
    getState: () => ({ activeTabId: "canvas-tab-1" }),
  },
}));

vi.mock("../executor/prepareTour", () => ({
  prepareTour: vi.fn().mockResolvedValue(undefined),
}));

vi.mock("../executor/restoreView", () => ({
  captureSavedView: vi.fn(() => ({
    tabId: "canvas-tab-1",
    selectedNodeId: null,
    secondarySelectedNodeId: null,
    expandedNodeIds: [],
    focusStack: [],
  })),
  restoreSavedView: vi.fn(),
}));

function seedBridgeState() {
  const parsed = mockFixtureSchema.parse(smallFunctionFixture);
  let session = null;
  let lastSeq = -1;
  let phase: "idle" | "generating" | "ready" | "error" = "idle";

  for (const entry of parsed.frames) {
    const result = applyFrame(entry.frame, { session, lastSeq, phase });
    session = result.session;
    lastSeq = result.lastSeq;
    phase = result.phase;
  }

  const playerSteps = session ? flattenSession(session) : [];

  useWalkthroughStore.setState({
    session,
    lastSeq,
    phase: "ready",
    error: null,
    playerSteps,
    cursor: -1,
    tabId: null,
  });
}

describe("play/jumpTo without tabId (chat path)", () => {
  beforeEach(() => {
    useWalkthroughStore.getState().discard();
  });

  it("play() resolves tabId from the active canvas tab and starts playing", async () => {
    seedBridgeState();

    useWalkthroughStore.getState().play();

    await vi.waitFor(() => {
      expect(useWalkthroughStore.getState().phase).toBe("playing");
    });

    const state = useWalkthroughStore.getState();
    expect(state.tabId).toBe("canvas-tab-1");
    expect(state.cursor).toBe(0);
    expect(state.preparing).toBe(false);
    expect(state.tourPrepared).toBe(true);
  });

  it("jumpTo(stepId) resolves tabId and jumps to the step index", async () => {
    seedBridgeState();
    const steps = useWalkthroughStore.getState().playerSteps;
    const target = steps[2]!;

    useWalkthroughStore.getState().jumpTo(target.id);

    await vi.waitFor(() => {
      expect(useWalkthroughStore.getState().phase).toBe("playing");
    });

    const state = useWalkthroughStore.getState();
    expect(state.tabId).toBe("canvas-tab-1");
    expect(state.cursor).toBe(2);
    expect(state.preparing).toBe(false);
    expect(state.tourPrepared).toBe(true);
  });
});

describe("isCurrentStepNode", () => {
  it("returns true only for the node at the current cursor while playing", () => {
    useWalkthroughStore.setState({
      phase: "playing",
      cursor: 1,
      playerSteps: [
        {
          id: "n00",
          nodeId: "root",
          actions: [],
          title: "Root",
          text: "intro",
          degraded: false,
          visitOrder: 0,
        },
        {
          id: "n01",
          nodeId: "child",
          actions: [],
          title: "Child",
          text: "intro",
          degraded: false,
          visitOrder: 1,
        },
      ],
    });

    expect(isCurrentStepNode("child")).toBe(true);
    expect(isCurrentStepNode("root")).toBe(false);
    expect(isCurrentStepNode("missing")).toBe(false);
  });
});

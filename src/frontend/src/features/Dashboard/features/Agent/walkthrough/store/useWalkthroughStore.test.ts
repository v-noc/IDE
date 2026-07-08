import { describe, expect, it } from "vitest";
import { isCurrentStepNode, useWalkthroughStore } from "./useWalkthroughStore";

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

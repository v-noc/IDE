import { describe, expect, it } from "vitest";
import { currentStepAnchor } from "./selectors";
import type { PlayerStep } from "../types";

function introStep(nodeId: string): PlayerStep {
  return {
    id: "n00",
    nodeId,
    actions: [{ type: "select_node", nodeId }],
    title: "intro",
    text: "hello",
    degraded: false,
    visitOrder: 0,
  };
}

function blockStep(nodeId: string, startLine: number): PlayerStep {
  return {
    id: "n00.b0",
    nodeId,
    actions: [
      { type: "show_code", nodeId },
      {
        type: "highlight_lines",
        nodeId,
        startLine,
        endLine: startLine + 5,
      },
    ],
    title: "block",
    text: "detail",
    degraded: false,
    visitOrder: 0,
  };
}

describe("currentStepAnchor", () => {
  it("returns null when not playing", () => {
    expect(
      currentStepAnchor({
        phase: "ready",
        cursor: 0,
        playerSteps: [introStep("a")],
      }),
    ).toBeNull();
  });

  it("returns node anchor for intro steps", () => {
    expect(
      currentStepAnchor({
        phase: "playing",
        cursor: 0,
        playerSteps: [introStep("services/payment/charge")],
      }),
    ).toEqual({ type: "node", nodeId: "services/payment/charge" });
  });

  it("returns code-line anchor for block steps", () => {
    expect(
      currentStepAnchor({
        phase: "playing",
        cursor: 0,
        playerSteps: [blockStep("services/payment/charge", 42)],
      }),
    ).toEqual({
      type: "code-line",
      nodeId: "services/payment/charge",
      line: 42,
    });
  });
});

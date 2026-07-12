import { describe, expect, it } from "vitest";
import smallFunctionFixture from "../fixtures/smallFunction.json";
import classWithCallFixture from "../fixtures/classWithCall.json";
import { applyFrame } from "../source/applyFrame";
import { flattenSession } from "./flatten";
import { mockFixtureSchema, walkthroughSessionSchema } from "../types";

function applyAllFrames(fixture: unknown) {
  const parsed = mockFixtureSchema.parse(fixture);
  let session = null;
  let lastSeq = -1;
  let phase: "idle" | "generating" | "ready" | "error" = "idle";

  for (const entry of parsed.frames) {
    const result = applyFrame(entry.frame, { session, lastSeq, phase });
    session = result.session;
    lastSeq = result.lastSeq;
    phase = result.phase;
  }

  return { session, phase };
}

describe("walkthrough fixtures", () => {
  it("parses smallFunction fixture frames", () => {
    const fixture = mockFixtureSchema.parse(smallFunctionFixture);
    expect(fixture.frames.length).toBeGreaterThan(0);
    for (const entry of fixture.frames) {
      expect(entry.frame.kind).toBeDefined();
    }
  });

  it("applies smallFunction patches to a complete session", () => {
    const { session, phase } = applyAllFrames(smallFunctionFixture);
    expect(phase).toBe("ready");
    expect(session).not.toBeNull();

    const parsed = walkthroughSessionSchema.parse(session);
    expect(parsed.status).toBe("complete");
    expect(parsed.node_steps).toHaveLength(1);
    expect(parsed.node_steps[0].blocks).toHaveLength(3);
    expect(parsed.node_steps[0].intro_text.length).toBeGreaterThan(0);
  });

  it("applies classWithCall patches to a complete session", () => {
    const { session, phase } = applyAllFrames(classWithCallFixture);
    expect(phase).toBe("ready");
    expect(session?.node_steps).toHaveLength(4);
  });
});

describe("flattenSession", () => {
  it("produces stable ids for a full code stop with blocks", () => {
    const { session } = applyAllFrames(smallFunctionFixture);
    const steps = flattenSession(session!);

    expect(steps.map((s) => s.id)).toEqual([
      "n00",
      "n00.b0",
      "n00.b1",
      "n00.b2",
    ]);
    expect(steps[0].actions).toEqual([
      { type: "select_node", nodeId: "services/payment/charge" },
      { type: "show_code", nodeId: "services/payment/charge" },
    ]);
    expect(steps[1].actions).toEqual([
      { type: "show_code", nodeId: "services/payment/charge" },
      {
        type: "highlight_lines",
        nodeId: "services/payment/charge",
        startLine: 10,
        endLine: 22,
      },
    ]);
  });

  it("keeps intro-only steps for contextual stops", () => {
    const { session } = applyAllFrames(classWithCallFixture);
    const steps = flattenSession(session!);
    const contextual = steps.filter((step) => step.id === "n03");

    expect(contextual).toHaveLength(1);
    expect(contextual[0].actions).toEqual([
      {
        type: "select_node",
        nodeId: "services/payment/calls/validate_card-ctx",
      },
    ]);
  });
});

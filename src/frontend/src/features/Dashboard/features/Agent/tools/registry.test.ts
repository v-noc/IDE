import { describe, expect, it } from "vitest";
import { isAvailable, TOOL_REGISTRY } from "./registry";

describe("tool registry", () => {
  it("lists four tools with one available", () => {
    expect(TOOL_REGISTRY).toHaveLength(4);
    expect(TOOL_REGISTRY.filter((t) => t.status === "available")).toHaveLength(1);
  });

  it("gates coming-soon tools", () => {
    expect(isAvailable("walkthrough")).toBe(true);
    expect(isAvailable("describe")).toBe(false);
    expect(isAvailable("document")).toBe(false);
    expect(isAvailable("group")).toBe(false);
    expect(isAvailable("unknown")).toBe(false);
  });
});

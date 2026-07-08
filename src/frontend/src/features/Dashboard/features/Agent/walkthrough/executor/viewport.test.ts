import { describe, expect, it } from "vitest";
import { isNodeFullyInViewport } from "./viewport";

describe("isNodeFullyInViewport", () => {
  const canvas = { width: 1000, height: 800 };

  it("returns true when the node fits with margin", () => {
    const viewport = { x: 100, y: 50, zoom: 1 };
    const node = { x: 200, y: 100, width: 120, height: 80 };

    expect(isNodeFullyInViewport(viewport, canvas, node)).toBe(true);
  });

  it("returns false when the node extends past the canvas edge", () => {
    const viewport = { x: 0, y: 0, zoom: 1 };
    const node = { x: 900, y: 100, width: 200, height: 80 };

    expect(isNodeFullyInViewport(viewport, canvas, node)).toBe(false);
  });

  it("accounts for zoom when mapping flow coordinates to screen space", () => {
    const viewport = { x: 0, y: 0, zoom: 0.5 };
    const node = { x: 100, y: 100, width: 200, height: 100 };

    expect(isNodeFullyInViewport(viewport, canvas, node, 0)).toBe(true);
  });
});

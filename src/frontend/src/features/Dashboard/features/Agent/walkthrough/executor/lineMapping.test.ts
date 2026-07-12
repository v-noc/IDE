import { describe, expect, it } from "vitest";
import {
  absoluteToEditorLine,
  clampEditorRange,
} from "../executor/lineMapping";

describe("lineMapping", () => {
  it("maps absolute file lines to editor lines", () => {
    expect(absoluteToEditorLine(10, 10)).toBe(1);
    expect(absoluteToEditorLine(23, 10)).toBe(14);
    expect(absoluteToEditorLine(62, 10)).toBe(53);
  });

  it("clamps ranges to the editor line count", () => {
    expect(clampEditorRange(0, 5, 40)).toEqual({ startLine: 1, endLine: 5 });
    expect(clampEditorRange(38, 50, 40)).toEqual({
      startLine: 38,
      endLine: 40,
    });
  });
});

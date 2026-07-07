/**
 * Maps absolute file line numbers to Monaco editor line numbers for a node slice.
 */
export function absoluteToEditorLine(
  absoluteLine: number,
  nodeStartLine: number,
): number {
  return absoluteLine - nodeStartLine + 1;
}

export function clampEditorRange(
  startLine: number,
  endLine: number,
  editorLineCount: number,
): { startLine: number; endLine: number } {
  const start = Math.max(1, Math.min(startLine, editorLineCount));
  const end = Math.max(start, Math.min(endLine, editorLineCount));
  return { startLine: start, endLine: end };
}

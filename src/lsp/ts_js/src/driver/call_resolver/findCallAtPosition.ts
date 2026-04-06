import ts from "typescript";
import { SyntaxKind, type CallExpression, type SourceFile } from "ts-morph";

/** Match `CallNode.call_col_pos` to the `(` token column (Python column convention). */
export function findCallExpressionAt(
  sourceFile: SourceFile,
  line: number,
  callColPos: number,
): CallExpression | undefined {
  const sf = sourceFile.compilerNode;
  const candidates = sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression);
  for (const c of candidates) {
    const open = c.getFirstChildByKind(SyntaxKind.OpenParenToken);
    if (!open) continue;
    const pos = open.getStart();
    const lc = ts.getLineAndCharacterOfPosition(sf, pos);
    if (lc.line + 1 !== line || lc.character !== callColPos) continue;
    return c;
  }
  return undefined;
}

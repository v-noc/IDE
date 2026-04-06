import ts from "typescript";
import type { Node } from "ts-morph";
import type { NodePosition } from "../models";

/** Python / parso convention: 1-based line, 0-based column. */
export function getNodePosition(node: Node): NodePosition {
  const sf = node.getSourceFile().compilerNode;
  const start = node.getStart(true);
  const end = node.getEnd() - 1;
  const s = ts.getLineAndCharacterOfPosition(sf, start);
  const e = ts.getLineAndCharacterOfPosition(sf, Math.max(start, end));
  return {
    line: s.line + 1,
    column: s.character,
    end_line: e.line + 1,
    end_column: e.character,
  };
}

export function positionKey(p: NodePosition): string {
  return `${p.line}:${p.column}:${p.end_line}:${p.end_column}`;
}

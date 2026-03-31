import path from "node:path";
import { Node, type Symbol as TsSymbol } from "ts-morph";
import {
  extractIdFromJsDocs,
  formatClassId,
  formatFunctionId,
} from "../ast/jsdocIds";

export function resolveAliasedSymbol(symbol: TsSymbol): TsSymbol {
  let s = symbol;
  const seen = new Set<TsSymbol>();
  while (s.isAlias()) {
    const next = s.getAliasedSymbol();
    if (!next || seen.has(next)) break;
    seen.add(s);
    s = next;
  }
  return s;
}

export function isProjectSource(filePath: string, projectRoot: string): boolean {
  const norm = path.normalize(filePath);
  const root = path.normalize(projectRoot);
  if (!norm.startsWith(root)) return false;
  if (norm.includes(`${path.sep}node_modules${path.sep}`)) return false;
  return true;
}

function jsdocText(node: Node): string {
  if (!Node.isJSDocable(node)) return "";
  return node.getJsDocs().map((d) => d.getInnerText()).join("\n");
}

/**
 * `FunctionSchema/…` or `ClassSchema/…` from JSDoc `ID:` only — matches Python
 * `_extract_id_from_docstring` + schema prefix; if missing, caller skips the frame
 * (`if target_id is None: continue` in `jedi_adapter.call_resolver`).
 */
export function schemaTargetIdFromDeclaration(decl: Node): string | undefined {
  if (!Node.isJSDocable(decl)) return undefined;
  const id = extractIdFromJsDocs(jsdocText(decl));
  if (!id) return undefined;
  if (Node.isClassDeclaration(decl)) return formatClassId(id);
  return formatFunctionId(id);
}

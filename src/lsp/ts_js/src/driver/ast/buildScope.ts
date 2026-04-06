import {
  Node,
  SyntaxKind,
  type Block,
  type CallExpression,
  type ClassDeclaration,
  type ConstructorDeclaration,
  type FunctionDeclaration,
  type MethodDeclaration,
  type SourceFile,
  type Statement,
} from "ts-morph";
import type {
  BaseNodeJson,
  CallNodeJson,
  ClassNodeJson,
  FunctionNodeJson,
} from "../models";
import { extractIdFromJsDocs, formatClassId, formatFunctionId } from "./jsdocIds";
import { getNodePosition, positionKey } from "./positions";

function jsdocInnerText(node: { getJsDocs: () => { getInnerText: () => string }[] }): string {
  return node.getJsDocs().map((d) => d.getInnerText()).join("\n");
}

function dedupeByPosition(nodes: BaseNodeJson[]): BaseNodeJson[] {
  const seen = new Set<string>();
  const out: BaseNodeJson[] = [];
  for (const n of nodes) {
    const k = positionKey(n.position);
    if (seen.has(k)) continue;
    seen.add(k);
    out.push(n);
  }
  return out;
}

function getBaseClassNames(cls: ClassDeclaration, resolveMro: boolean): string[] {
  if (!resolveMro) return [];
  const ext = cls.getExtends();
  if (!ext) return [];
  return [ext.getText().trim()];
}

function visitCall(call: CallExpression, counter: { n: number }): CallNodeJson {
  const callee = call.getExpression().getText();
  const pos = getNodePosition(call);
  const open = call.getFirstChildByKind(SyntaxKind.OpenParenToken);
  const colPos = open ? getNodePosition(open).column : pos.column;
  const idx = counter.n++;
  return {
    type: "call",
    name: callee,
    position: pos,
    children: [],
    call_index: idx,
    call_col_pos: colPos,
    id: null,
  };
}

function collectCallsFromNode(root: Node, counter: { n: number }): CallNodeJson[] {
  const calls: CallNodeJson[] = [];
  root.forEachDescendant((node, traversal) => {
    if (Node.isClassDeclaration(node) || Node.isFunctionDeclaration(node)) {
      traversal.skip();
      return;
    }
    if (Node.isCallExpression(node)) {
      calls.push(visitCall(node, counter));
    }
  });
  return calls;
}

function visitBlock(block: Block, resolveMro: boolean): BaseNodeJson[] {
  return visitStatements(block.getStatements(), resolveMro);
}

function visitClass(cls: ClassDeclaration, resolveMro: boolean): ClassNodeJson {
  const idRaw = extractIdFromJsDocs(jsdocInnerText(cls));
  const children = visitClassBody(cls, resolveMro);
  return {
    type: "class",
    id: idRaw ? formatClassId(idRaw) : null,
    name: cls.getName() ?? "",
    position: getNodePosition(cls),
    base_classes: getBaseClassNames(cls, resolveMro),
    children,
  };
}

function visitClassBody(cls: ClassDeclaration, resolveMro: boolean): BaseNodeJson[] {
  const out: BaseNodeJson[] = [];
  const counter = { n: 0 };

  for (const m of cls.getMembers()) {
    if (Node.isMethodDeclaration(m)) {
      const fn = visitMethod(m, resolveMro);
      if (fn) out.push(fn);
      continue;
    }
    if (Node.isConstructorDeclaration(m)) {
      const fn = visitConstructor(m, resolveMro);
      if (fn) out.push(fn);
      continue;
    }
    if (Node.isClassStaticBlockDeclaration(m)) {
      const b = m.getBody();
      if (b && Node.isBlock(b)) out.push(...visitBlock(b, resolveMro));
      continue;
    }
    if (Node.isClassDeclaration(m)) {
      out.push(visitClass(m, resolveMro));
      continue;
    }
    if (Node.isPropertyDeclaration(m)) {
      const init = m.getInitializer();
      if (init) {
        out.push(...collectCallsFromNode(init, counter));
      }
    }
  }

  return dedupeByPosition(out);
}

function visitFunctionDecl(fn: FunctionDeclaration, resolveMro: boolean): FunctionNodeJson | null {
  const body = fn.getBody();
  if (!body || !Node.isBlock(body)) return null;
  const idRaw = extractIdFromJsDocs(jsdocInnerText(fn));
  const name = fn.getName() ?? "";
  const children = visitBlock(body, resolveMro);
  return {
    type: "function",
    id: idRaw ? formatFunctionId(idRaw) : null,
    name,
    position: getNodePosition(fn),
    children,
  };
}

function visitMethod(m: MethodDeclaration, resolveMro: boolean): FunctionNodeJson | null {
  const body = m.getBody();
  if (!body || !Node.isBlock(body)) return null;
  const idRaw = extractIdFromJsDocs(jsdocInnerText(m));
  const name = m.getName() ?? "";
  const children = visitBlock(body, resolveMro);
  return {
    type: "function",
    id: idRaw ? formatFunctionId(idRaw) : null,
    name,
    position: getNodePosition(m),
    children,
  };
}

function visitConstructor(c: ConstructorDeclaration, resolveMro: boolean): FunctionNodeJson | null {
  const body = c.getBody();
  if (!body || !Node.isBlock(body)) return null;
  const idRaw = extractIdFromJsDocs(jsdocInnerText(c));
  const children = visitBlock(body, resolveMro);
  return {
    type: "function",
    id: idRaw ? formatFunctionId(idRaw) : null,
    name: "constructor",
    position: getNodePosition(c),
    children,
  };
}

function visitStatement(st: Statement, resolveMro: boolean): BaseNodeJson[] {
  const counter = { n: 0 };

  if (Node.isClassDeclaration(st)) {
    return [visitClass(st, resolveMro)];
  }
  if (Node.isFunctionDeclaration(st)) {
    const fn = visitFunctionDecl(st, resolveMro);
    return fn ? [fn] : [];
  }

  const structured: BaseNodeJson[] = [];
  st.forEachDescendant((node, traversal) => {
    if (Node.isClassDeclaration(node)) {
      structured.push(visitClass(node, resolveMro));
      traversal.skip();
      return;
    }
    if (Node.isFunctionDeclaration(node)) {
      const fn = visitFunctionDecl(node, resolveMro);
      if (fn) structured.push(fn);
      traversal.skip();
      return;
    }
  });

  const calls = collectCallsFromNode(st, counter);
  return dedupeByPosition([...structured, ...calls]);
}

export function visitStatements(
  statements: readonly Statement[],
  resolveMro: boolean,
): BaseNodeJson[] {
  const out: BaseNodeJson[] = [];
  for (const st of statements) {
    out.push(...visitStatement(st, resolveMro));
  }
  return dedupeByPosition(out);
}

export function buildNodesFromSourceFile(
  sf: SourceFile,
  resolveMro: boolean,
): BaseNodeJson[] {
  return visitStatements(sf.getStatements(), resolveMro);
}

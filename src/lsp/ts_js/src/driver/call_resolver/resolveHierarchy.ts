import {
  Node,
  SyntaxKind,
  type CallExpression,
  type ConstructorDeclaration,
  type NewExpression,
  type Symbol as TsSymbol,
} from "ts-morph";
import { collectCallExpressionsSkippingNestedScopes } from "./collectCalls";
import { addChild, type CallFrameNode, isAncestor } from "./frame";
import {
  isProjectSource,
  resolveAliasedSymbol,
  schemaTargetIdFromDeclaration,
} from "./projectPaths";

function resolveExpressionSymbolForCall(callExpr: CallExpression): TsSymbol | undefined {
  const expr = callExpr.getExpression();
  const sym = expr.getSymbol();
  if (sym) return sym;
  if (expr.getKind() === SyntaxKind.PropertyAccessExpression) {
    return expr.getSymbol();
  }
  return undefined;
}

function getPrimaryFunctionLikeDeclaration(symbol: TsSymbol): Node | undefined {
  const resolved = resolveAliasedSymbol(symbol);
  for (const decl of resolved.getDeclarations() ?? []) {
    if (Node.isFunctionLikeDeclaration(decl)) {
      return decl;
    }
  }
  return undefined;
}

function getClassConstructor(classDecl: Node): ConstructorDeclaration | undefined {
  if (!Node.isClassDeclaration(classDecl)) return undefined;
  return classDecl.getConstructors()[0];
}

function resolveNewToConstructorLike(
  newExpr: NewExpression,
): ConstructorDeclaration | undefined {
  const expr = newExpr.getExpression();
  const sym = expr.getSymbol();
  if (!sym) return undefined;
  const resolved = resolveAliasedSymbol(sym);
  for (const decl of resolved.getDeclarations() ?? []) {
    if (Node.isClassDeclaration(decl)) {
      return getClassConstructor(decl) ?? undefined;
    }
  }
  return undefined;
}

function getBodyNode(fn: Node): Node | undefined {
  if (Node.isFunctionDeclaration(fn)) return fn.getBody() ?? undefined;
  if (Node.isMethodDeclaration(fn)) return fn.getBody() ?? undefined;
  if (Node.isConstructorDeclaration(fn)) return fn.getBody() ?? undefined;
  if (Node.isArrowFunction(fn)) return fn.getBody() ?? undefined;
  if (Node.isFunctionExpression(fn)) return fn.getBody() ?? undefined;
  if (Node.isGetAccessorDeclaration(fn)) return fn.getBody() ?? undefined;
  if (Node.isSetAccessorDeclaration(fn)) return fn.getBody() ?? undefined;
  return undefined;
}

function analyzeFunctionLikeBody(
  fn: Node,
  currentFrame: CallFrameNode,
  projectRoot: string,
): void {
  if (!Node.isFunctionLikeDeclaration(fn)) return;
  const body = getBodyNode(fn);
  if (!body) return;
  const calls = collectCallExpressionsSkippingNestedScopes(body);
  for (const call of calls) {
    resolveCallHierarchyForNode(call, currentFrame, projectRoot);
  }
}

export function resolveCallHierarchyForNode(
  callExpr: CallExpression,
  parentFrame: CallFrameNode,
  projectRoot: string,
): void {
  const sym = resolveExpressionSymbolForCall(callExpr);
  if (!sym) return;

  const resolved = resolveAliasedSymbol(sym);
  const decls = resolved.getDeclarations();
  if (!decls.length) return;

  const primary = decls[0];
  if (!primary) return;
  const declFile = primary.getSourceFile().getFilePath();
  if (!isProjectSource(declFile, projectRoot)) return;

  const targetId = schemaTargetIdFromDeclaration(primary);
  if (targetId === undefined) return;

  const qname = resolved.getFullyQualifiedName();
  if (isAncestor(parentFrame, qname)) return;

  const newFrame = addChild(parentFrame, {
    targetQName: qname,
    targetId,
    children: [],
    callCount: 1,
  });

  const fnLike = getPrimaryFunctionLikeDeclaration(resolved);
  if (fnLike) {
    analyzeFunctionLikeBody(fnLike, newFrame, projectRoot);
    return;
  }

  if (Node.isClassDeclaration(primary)) {
    const ctor = getClassConstructor(primary);
    if (ctor) {
      analyzeFunctionLikeBody(ctor, newFrame, projectRoot);
    }
  }
}

export function resolveNewHierarchyForNode(
  newExpr: NewExpression,
  parentFrame: CallFrameNode,
  projectRoot: string,
): void {
  const ctor = resolveNewToConstructorLike(newExpr);
  if (!ctor) return;
  const sourceFile = ctor.getSourceFile().getFilePath();
  if (!isProjectSource(sourceFile, projectRoot)) return;

  const sym = ctor.getSymbol();
  if (!sym) return;
  const resolved = resolveAliasedSymbol(sym);
  const targetId = schemaTargetIdFromDeclaration(ctor);
  if (targetId === undefined) return;

  const qname = resolved.getFullyQualifiedName();
  if (isAncestor(parentFrame, qname)) return;

  const newFrame = addChild(parentFrame, {
    targetQName: qname,
    targetId,
    children: [],
    callCount: 1,
  });
  analyzeFunctionLikeBody(ctor, newFrame, projectRoot);
}

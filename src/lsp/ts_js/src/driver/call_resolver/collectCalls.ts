import { Node, SyntaxKind, type CallExpression } from "ts-morph";

/**
 * Collect `CallExpression` nodes, skipping nested function/class bodies
 * (same idea as the Python walk skipping inner `Function` / `Class`).
 */
export function collectCallExpressionsSkippingNestedScopes(root: Node): CallExpression[] {
  const out: CallExpression[] = [];
  function visit(node: Node): void {
    const k = node.getKind();
    if (
      k === SyntaxKind.FunctionDeclaration ||
      k === SyntaxKind.ClassDeclaration ||
      k === SyntaxKind.FunctionExpression ||
      k === SyntaxKind.ArrowFunction
    ) {
      return;
    }
    if (k === SyntaxKind.CallExpression) {
      out.push(node as CallExpression);
    }
    for (const c of node.getChildren()) {
      visit(c);
    }
  }
  visit(root);
  return out;
}
